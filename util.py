import time
import uuid
import re
import os

from werkzeug.exceptions import BadRequest, Unauthorized

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import request, g, session
from flask_restful import reqparse
from flask_socketio import emit

from dotenv import load_dotenv

import mysql.connector
import base64

from dao.auth import WebsiteAuth
from dao.member import Member
from dao.player import Player

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

STRONG_PASSWORD_REG = re.compile(r"^(?=.*[A-Z])(?=.*)(?=.*[0-9])(?=.*[a-z]).{8,}$")
EMAIL_REG = re.compile(r"[\w\.-]+@[\w\.-]+(\.[\w]+)+")

with open("email_verification.html", "r") as f: EMAIL_VERIFICATION_MESSAGE = f.read()

database = mysql.connector.connect(host=os.getenv("MYSQL_HOST"), database=os.getenv("MYSQL_DATABASE"), user=os.getenv("MYSQL_USER"), password=os.getenv("MYSQL_PASSWORD"))
cursor = database.cursor(dictionary=True)
#cursor.execute("DELETE FROM members;")
#cursor.execute("DELETE FROM website_authentication;")
#database.commit()

awaiting_verification : dict[str:dict["expires": str, "auth": WebsiteAuth]] = {}

def requires_authentication(type : Member | Player, allow_guests : bool = False):
    """
    Require the author of the request to be authenticated (suppors socket requests).

    .. code-block:: python
        @app.route("...")
        @requires_authentication(type=Member | Player, allow_guests=...)
        def route(...)
    
    :param type: the type of user you want to authenticate
    :param allow_guests: can the request author be authenticated as a guest
    """

    if allow_guests and type == Member: raise ValueError("Type Member cannot be guest")
    def decorator(function):
        def wrapper(*args, **kwargs):
            if allow_guests: user = Player.create_guest()
            else:
                if not "session_token" in session: raise Unauthorized

                user : Member = Member.select(session_token=session["session_token"])
                if not user: raise Unauthorized

                user = user[0]

            return function(*args, user=user, **kwargs)

        wrapper.__name__ = function.__name__
        return wrapper
    return decorator

def requires_arguments(*arguments : reqparse.Argument):
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
            if request.path != "/socket.io/": return function(*args, args=_parse_arguments(*arguments), **kwargs)

            try: parsed = _parse_arguments(*arguments)
            except BadRequest: return
            function(*args, args=parsed, **kwargs)

        wrapper.__name__ = function.__name__
        return wrapper
    return decorator

def _parse_arguments(*arguments):
    is_socket = request.path == "/socket.io/"
    if is_socket: g.json = request.event["args"][0]
    elif not request.is_json: raise BadRequest("Invalid Json")

    parser = reqparse.RequestParser()
    for argument in arguments: parser.add_argument(argument)

    try: args = parser.parse_args(g if is_socket else None)
    except BadRequest as error:
        message = "\n".join([f"{argument}: {help}" for argument, help in error.data["message"].items()])
        if is_socket: emit("exception", SocketIOExceptions.BAD_ARGUMENT)
        raise BadRequest("Missing Arguments:\n" + message)

    return args

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
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(os.path.join(working_dir, token_dir, token_file), "w") as token:
            token.write(creds.to_json())

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
    id = uuid.uuid4().hex
    awaiting_verification[id] = {"expires": time.time() + 60 * 10, "auth": auth}

    message = MIMEMultipart("alternative")
    message["To"] = to
    message["Subject"] = "Chess 2 Email Verification"

    message.attach(MIMEText(EMAIL_VERIFICATION_MESSAGE.replace("{VERIFICATION-ID}", id), "html"))

    gmail_service.users().messages().send(userId="me", body={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}).execute()

class SocketIOExceptions:
    BAD_ARGUMENT = 0