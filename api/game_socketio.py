from flask_restful.reqparse import Argument

from util import requires_auth, requires_args, try_get_user_from_session, socket_error_handler, SocketIOException, SocketIOErrors
from dao import User, Game, active_games
from app import socketio

def requires_game(function):
    @requires_auth(allow_guests=True)
    def wrapper(*args, **kwargs):
        user = kwargs.get("user")
        if not user: user = try_get_user_from_session(allow_guests=True)

        game : Game = Game.query.filter((Game.white == user) | (Game.black == user)).first()
        if not game: raise SocketIOException(SocketIOErrors.BAD_REQUEST, "Unknown Game Token")

        return function(*args, game=game, **kwargs)
    wrapper.__name__ == function.__name__
    return wrapper

@socketio.on("move", namespace="/game")
@socket_error_handler
@requires_args(
    Argument("origin_x", type=int, required=True), Argument("origin_y", type=int, required=True),
    Argument("destination_x", type=int, required=True), Argument("destination_y", type=int, required=True)
)
@requires_game
def move(_, user : User, game : Game, args):
    active_games[game.token].move(
        user,
        origin={"x": args.origin_x, "y": args.origin_y},
        destination={"x": args.destination_x, "y": args.destination_y}
    )