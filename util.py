from werkzeug.exceptions import BadRequest

from flask_restful import reqparse
from flask_socketio import emit
from flask import request, g

from member import Member, Player

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
            if request.path == "/socket.io/": raise NotImplementedError()

            if allow_guests: user = Player.create_guest()
            else:
                # TODO: registed user authentication
                parsed = _parse_arguments(reqparse.Argument("session_token", type=str, help="Token generated when the session started"))
                user = None

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