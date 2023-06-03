from flask_restful.reqparse import Argument

from util import requires_auth, requires_args, socket_error_handler, SocketIOException, SocketIOErrors
from app import socketio
from dao import User

@socketio.on("move", namespace="/game")
@socket_error_handler
@requires_auth(allow_guests=True)
@requires_args(
    Argument("origin_x", type=int, required=True), Argument("origin_y", type=int, required=True),
    Argument("destination_x", type=int, required=True), Argument("destination_y", type=int, required=True),
    Argument("promote_to", type=str, default=None)
)
def move(_, user : User, args):
    if not user.active_game: raise SocketIOException(SocketIOErrors.NOT_FOUND, "No Active Game")
    user.active_game.get_game_class().move(
        user,
        origin={"x": args.origin_x, "y": args.origin_y},
        destination={"x": args.destination_x, "y": args.destination_y},
        args=args
    )

@socket_error_handler
@requires_auth(allow_guests=True)
def basic_route(function_name, user : User):
    if not user.active_game: raise SocketIOException(SocketIOErrors.NOT_FOUND, "No Active Game")
    getattr(user.active_game.get_game_class(), function_name)(user)

BASIC_ROUTES = ["resign", "request_draw", "decline_draw", "accept_draw", "ignore_draw_requests"]
for route in BASIC_ROUTES: socketio.on(route, namespace="/game")(lambda route=route: basic_route(function_name=route))