from contextlib import contextmanager
from datetime import datetime

import base64
import time
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

from dao import EmailVerification, SessionToken, WebsiteAuth, Member, PoolConn
from extensions import EMAIL_VERIFICATION_MESSAGE

def requires_auth(allow_guests : bool=False):
    """
    Require the author of the request to be authenticated (suppors socket requests).

    .. code-block:: python
        @app.route("...")
        @requires_authentication(type=Member | Player, allow_guests=...)
        def route(...)
    
    :param type: the type of user you want to authenticate
    :param allow_guests: can the request author be authenticated as a guest
    """

    def decorator(function):
        def wrapper(*args, **kwargs):
            # Create a guest user / get the user from the session
            if allow_guests: user = Member.create_guest()
            else: user = try_get_user_from_session()

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
                if is_socket:
                    emit("exception", SocketIOExceptions.BAD_ARGUMENT)
                    return
                else: raise BadRequest("Missing Arguments:\n" + message)

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

def socketio_db(function):
    def wrapper(*args, **kwargs):
        request.pool_conn = PoolConn()
        function(*args, **kwargs)
        if hasattr(request, "pool_conn") and not request.pool_conn._closed: request.pool_conn.close()
    return wrapper

def try_get_user_from_session(must_logged_in=True, raise_on_session_expired=True) -> Member | None:
    """
    Get the user object from the session.

    :param force_login: raise unauthorized exception when not logged in
    :param raise_on_session_expired: raise unauthorized exception when the user is logged in but the sesion expired
    """

    # Check if the user is logged in
    if not "session_token" in session:
        if must_logged_in: raise Unauthorized("Not Logged In")
        else: return

    # Select the token
    token : SessionToken = SessionToken.select(token=session["session_token"]).first()
    if not token:
        # If it doesn't find the token, it means the session token has expired
        session.clear()
        if raise_on_session_expired: raise Unauthorized("Session Expired")
        return
    
    token.last_used = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    token.update()
    return Member.select(member_id=token.member_id).first()

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
    verification_data : EmailVerification = EmailVerification.select(member_id=auth.member_id).first()
    if verification_data:
        # If there is one, it will reset the expiry date
        token = verification_data.token
        
        verification_data.created_at = "CURRENT_TIMESTAMP"
        verification_data.update()
    else:
        # If there isn't one, it'll generate an id and save it
        token = uuid.uuid4().hex
        EmailVerification(member_id=auth.member_id, token=token).insert()

    # Create the email object
    message = MIMEMultipart("alternative")
    message["To"] = to
    message["Subject"] = "Chess 2 Email Verification"

    message.attach(MIMEText(EMAIL_VERIFICATION_MESSAGE.replace("{TOKEN}", token), "html"))

    # Send the email
    gmail_service.users().messages().send(userId="me", body={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}).execute()

class SocketIOExceptions:
    BAD_ARGUMENT = 0