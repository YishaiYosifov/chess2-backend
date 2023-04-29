from werkzeug.exceptions import BadRequest, Conflict, NotFound

from flask_restful.reqparse import Argument
from flask_socketio import emit
from flask import Blueprint

from dao import OutgoingGame, Game, Member, AuthMethods
from util import requires_args, requires_auth
from extensions import CONFIG
from app import db

game = Blueprint("game", __name__, url_prefix="/game")

@game.route("/pool/start", methods=["POST"])
@requires_args(Argument("mode", type=str, required=True), Argument("time_control", type=int, required=True))
@requires_auth()
def start_pool_game(user : Member, args):
    """
    Start a game with a random
    """

    if OutgoingGame.query.filter_by(member=user).first(): raise Conflict("You already have an outgoing game")

    # Check if the mode and the time control are valid
    mode : str = args.mode
    time_control : int = args.time_control
    if not mode in CONFIG["modes"]: raise BadRequest("Invalid Mode")
    if not time_control in CONFIG["time_controls"]: raise BadRequest("Invalid Time Control")

    # Loop over the game pool, if a game with a similar rating is in the pool, start the game
    pool : list[OutgoingGame] = OutgoingGame.query.filter_by(mode=mode, time_control=time_control, is_pool=True).order_by(OutgoingGame.created_at).all()
    for outgoing in pool:
        opponent : Member = outgoing.member
        if not opponent or \
                (opponent.auth_method == AuthMethods.GUEST and not user.auth_method == AuthMethods.GUEST): continue
        
        if abs(opponent.rating.elo - user.rating.elo) <= CONFIG["acceptable_rating_difference"]:

            # Start the game
            game_id = Game.start_game(user, opponent, mode=mode, time_control=time_control)
            db.session.delete(outgoing)
            db.session.commit()

            # Return the game id to both players
            emit("game_started", {"game_id": game_id}, room=opponent.sid, namespace="/")
            return game_id
    
    # If a valid game was not found, add a new game to the pool
    db.session.add(OutgoingGame(member=user, mode=mode, time_control=time_control, is_pool=True))
    db.session.commit()
    return "Added to the pool", 200

@game.route("/cancel", methods=["POST"])
@requires_auth()
def cancel_pool_game(user : Member):
    outgoing = OutgoingGame.query.filter_by(member=user).first()
    if not outgoing: raise NotFound("No Outgoing Games")

    db.session.delete(outgoing)
    db.session.commit()
    return "Request Deleted", 200