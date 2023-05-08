from flask_restful.reqparse import Argument

from util import requires_auth, requires_args, try_get_user_from_session, SocketIOException, SocketIOErrors, socket_error_handler
from dao import User, Game, active_games
from app import socketio

def requires_game(function):
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

@requires_auth(allow_guests=True)
@requires_args(
    Argument("from_x", type=int, required=True), Argument("from_y", type=int, required=True),
    Argument("to_x", type=int, required=True), Argument("to_y", type=int, required=True)
)
@requires_game
def move(_, user : User, game : Game, args):
    active_games[game.token].move(
        user,
        origin={"x": args.from_x, "y": args.from_y},
        destination={"x": args.to_x, "y": args.to_y}
    )