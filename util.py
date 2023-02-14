import os

from werkzeug.exceptions import BadRequest, Unauthorized

from google_auth_oauthlib.flow import Flow

from flask import request, g, session
from flask_restful import reqparse
from flask_socketio import emit

from dotenv import load_dotenv

import mysql.connector

from dao.member import Member, Player

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
flow = Flow.from_client_secrets_file(
    client_secrets_file="google_auth.json",
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/google_login_callback")


database = mysql.connector.connect(host=os.getenv("MYSQL_HOST"), database=os.getenv("MYSQL_DATABASE"), user=os.getenv("MYSQL_USER"), password=os.getenv("MYSQL_PASSWORD"))
cursor = database.cursor(dictionary=True)

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

                user = Member.select(session_token=session["session_token"])
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

class SocketIOExceptions:
    BAD_ARGUMENT = 0