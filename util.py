from datetime import datetime
from enum import Enum

import base64
import uuid
import os

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from werkzeug.exceptions import BadRequest, Unauthorized

from flask import request, g, session
from flask_restful import reqparse
from flask_socketio import emit

from dao import EmailVerification, WebsiteAuth, User, AuthMethods
from extensions import EMAIL_VERIFICATION_MESSAGE
from app import db

def requires_auth(allow_guests : bool=False):
    """
    Require the author of the request to be authenticated (suppors socket requests).

    .. code-block:: python
        @app.route("...")
        @requires_authentication(type=User | Player, allow_guests=...)
        def route(...)
    
    :param type: the type of user you want to authenticate
    :param allow_guests: can the request author be authenticated as a guest
    """

    def decorator(function):
        def wrapper(*args, **kwargs):            
            # Create a guest user / get the user from the session
            try: user = try_get_user_from_session(allow_guests=allow_guests)
            except Unauthorized as exception:
                if allow_guests:
                    user = User.create_guest()
                    request.cached_session_user = user
                    db.session.commit()
                else:
                    if request.path == "/socket.io/": raise SocketIOException(SocketIOErrors.UNAUTHORIZED, exception.description)
                    raise
            else:
                if not allow_guests and user.auth_method == AuthMethods.GUEST: raise Unauthorized("Not Logged In")

            return function(*args, user=user, **kwargs)

        wrapper.__name__ = function.__name__
        return wrapper
    return decorator

def requires_args(*arguments : reqparse.Argument):
    """
    Require the request to include certain arguments (supports socket requests).

    .. code-block:: python
        @app.route("...")
        @requires_arguments(reqparse.Argument(...), reqparse.Argument(...))
        def route(...)

    :param arguments: the required arguments
    """
    def decorator(function):
        def wrapper(*args, **kwargs):
            is_socket = request.path == "/socket.io/"

            # Get the arguments from the request
            if is_socket: g.json = request.event["args"][0]
            elif not request.is_json: raise BadRequest("Invalid Json")

            # Create the argument parser object and add all the arguments
            parser = reqparse.RequestParser()
            for argument in arguments: parser.add_argument(argument)

            # Parse the arguments
            try: parsed = parser.parse_args(g if is_socket else None)
            except BadRequest as error:
                # If there are any missing / bad arguments, return them through socket io / http request
                message = "\n".join([f"{argument}: {help}" for argument, help in error.data["message"].items()])
                if is_socket: raise SocketIOException(SocketIOErrors.BAD_ARGUMENT, message)
                else: raise BadRequest("Missing / Bad Arguments:\n" + message)

            # If there are any empty arguments with a default value, set the arg to the default value
            for arg_name, value in parsed.copy().items():
                if value is None:
                    try: arg = next(filter(lambda arg: arg.name == arg_name, parser.args))
                    except StopIteration: continue

                    if not arg.default is None: parsed[arg_name] = arg.default

            return function(*args, args=parsed, **kwargs)

        wrapper.__name__ = function.__name__
        return wrapper
    return decorator

def try_get_user_from_session(force_logged_in=True, allow_guests=False) -> User | None:
    """
    Get the user object from the session.

    :param must_logged_in: raise unauthorized exception when not logged in
    :param allow_guests: whether to allow guests users
    """

    if hasattr(request, "cached_session_user"): return request.cached_session_user

    # Check if the user is logged in
    if not "user_id" in session:
        if allow_guests:
            user = User.create_guest()
            db.session.commit()
            return user
        if force_logged_in: raise Unauthorized("Not Logged In")
        return

    # Get the user from the session
    user : User = User.query.filter_by(user_id=session["user_id"]).first()
    if not user:
        # If the user was not found, something went wrong
        session.clear()
        if force_logged_in: raise Unauthorized("Not Logged In")
        return
    elif not allow_guests and user.auth_method == AuthMethods.GUEST:
        if force_logged_in: raise Unauthorized("Not Logged In")
        return
    
    user.last_accessed = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.session.commit()

    request.cached_session_user = user
    return user

def create_gmail_service(client_secret_file, api_name, api_version, *scopes, prefix=""):
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]
    
    creds = None
    working_dir = os.getcwd()
    token_dir = "google_tokens"
    token_file = f"token_{API_SERVICE_NAME}_{API_VERSION}{prefix}.json"

    if not os.path.exists(os.path.join(working_dir, token_dir)): os.mkdir(os.path.join(working_dir, token_dir))

    if os.path.exists(os.path.join(working_dir, token_dir, token_file)): creds = Credentials.from_authorized_user_file(os.path.join(working_dir, token_dir, token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(os.path.join(working_dir, token_dir, token_file), "w") as token: token.write(creds.to_json())

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=creds, static_discovery=False)
        return service
    except Exception as e:
        print(e)
        print(f"Failed to create service instance for {API_SERVICE_NAME}")
        os.remove(os.path.join(working_dir, token_dir, token_file))
        return
gmail_service = create_gmail_service("google_tokens/email_auth.json", "gmail", "v1", ["https://mail.google.com/"])

def send_verification_email(to : str, auth : WebsiteAuth):
    """
    Send a verification email

    :param to: the email address of the user
    :param auth: the user's website auth object
    """

    # Check if there is already an active verification email
    verification_data : EmailVerification = EmailVerification.query.filter_by(user_id=auth.user_id).first()
    if verification_data:
        # If there is one, it will reset the expiry date
        token = verification_data.token
        
        verification_data.created_at = datetime.utcnow()
    else:
        # If there isn't one, it'll generate an id and save it
        token = uuid.uuid4().hex
        db.session.add(EmailVerification(user=auth.user, token=token))
    db.session.commit()

    # Create the email object
    message = MIMEMultipart("alternative")
    message["To"] = to
    message["Subject"] = "Chess 2 Email Verification"

    message.attach(MIMEText(EMAIL_VERIFICATION_MESSAGE.replace("{TOKEN}", token), "html"))

    # Send the email
    gmail_service.users().messages().send(userId="me", body={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}).execute()

def column_to_dict(column, include = [], exclude = []) -> dict[str:any]:
    """
    Get attributes from sqlalchemy object

    :param include: attributes to include
    :param exclude: attributes to exclude

    :raises ValueError: both include and exclude were given
    """
    if include and exclude: raise ValueError("Cannot have both include and exclude")

    results = {}
    for attribute in column.__table__.columns:
        name = attribute.name
        if (include and not name in include) or name in exclude or name.startswith("_"): continue
        
        value = getattr(column, name)
        if isinstance(value, Enum): value = value.value
        elif isinstance(value, datetime): value = value.isoformat()
        results[name] = value
    return results

class SocketIOErrors(Enum):
    BAD_ARGUMENT = 0
    UNAUTHORIZED = 1

    BAD_REQUEST = 2
    CONFLICT = 3

    MOVE_ERROR = 4
    FORCED_MOVE_ERROR = 5

    PROMOTION_ERROR = 6
    SERVER_ERROR = 7
    NOT_FOUND = 8
class SocketIOException(Exception):
    def __init__(self, code : SocketIOErrors, message : str):
        super().__init__(message)
        
        self.code = code.value
        self.message = message

def socket_error_handler(function):
    def wrapper(*args, **kwargs):
        try: return function(*args, **kwargs)
        except Exception as e:
            if isinstance(e, SocketIOException): emit("exception", {"code": e.code, "message": e.message})
            else:
                emit("exception", {"code": SocketIOErrors.SERVER_ERROR.value, "message": "Internal Server Error"})
                raise
    wrapper.__name__ = function.__name__
    return wrapper