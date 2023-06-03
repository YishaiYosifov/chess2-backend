from flask_restful.reqparse import Argument

from util import requires_auth, requires_args, socket_error_handler, SocketIOException, SocketIOErrors
from app import socketio
from dao import User

@socketio.on("move", namespace="/game")
@socket_error_handler
@requires_args(
    Argument("origin_x", type=int, required=True), Argument("origin_y", type=int, required=True),
    Argument("destination_x", type=int, required=True), Argument("destination_y", type=int, required=True),
    Argument("promote_to", type=str, default=None)
)
@requires_auth(allow_guests=True)
def move(user : User, args):
    if not user.active_game: raise SocketIOException(SocketIOErrors.BAD_REQUEST, "No Active Game")
    user.active_game.get_game_class().move(
        user,
        origin={"x": args.origin_x, "y": args.origin_y},
        destination={"x": args.destination_x, "y": args.destination_y},
        args=args
    )

@socketio.on("resign", namespace="/game")
@socket_error_handler
@requires_auth(allow_guests=True)
def resign(user : User):
    if not user.active_game: raise SocketIOException(SocketIOErrors.BAD_REQUEST, "No Active Game")
    user.active_game.get_game_class().resign(user)