from flask_restful.reqparse import Argument

from util import requires_auth, requires_args, try_get_user_from_session, socket_error_handler, SocketIOException, SocketIOErrors
from app import socketio, db
from dao import User, Game

def requires_game(function):
    @requires_auth(allow_guests=True)
    def wrapper(*args, **kwargs):
        user = kwargs.get("user")
        if not user: user = try_get_user_from_session(allow_guests=True)

        game : Game = Game.query.filter((Game.is_over == db.false()) & (Game.white.has(user=user) | Game.black.has(user=user))).first()
        if not game: raise SocketIOException(SocketIOErrors.BAD_REQUEST, "Unknown Game Token")

        return function(*args, game=game, **kwargs)
    wrapper.__name__ == function.__name__
    return wrapper

@socketio.on("move", namespace="/game")
@socket_error_handler
@requires_args(
    Argument("origin_x", type=int, required=True), Argument("origin_y", type=int, required=True),
    Argument("destination_x", type=int, required=True), Argument("destination_y", type=int, required=True),
    Argument("promote_to", type=str, default=None)
)
@requires_game
def move(_, user : User, game : Game, args):
    game.get_game_class().move(
        user,
        origin={"x": args.origin_x, "y": args.origin_y},
        destination={"x": args.destination_x, "y": args.destination_y},
        args=args
    )