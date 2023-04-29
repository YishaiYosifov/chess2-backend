from werkzeug.exceptions import BadRequest, Conflict, NotFound

from flask_restful.reqparse import Argument
from flask_socketio import emit
from flask import Blueprint

from dao import OutgoingGames, Game, User, AuthMethods
from util import requires_args, requires_auth
from extensions import CONFIG
from app import db

game = Blueprint("game", __name__, url_prefix="/game")

@game.route("/pool/start", methods=["POST"])
@requires_args(Argument("mode", type=str, required=True), Argument("time_control", type=int, required=True))
@requires_auth()
def start_pool_game(user : User, args):
    """
    Start a game with a random
    """

    if user.outgoing_game: raise Conflict("You already have an outgoing game")

    # Check if the mode and the time control are valid
    mode : str = args.mode
    time_control : int = args.time_control
    if not mode in CONFIG["MODES"]: raise BadRequest("Invalid Mode")
    if not time_control in CONFIG["TIME_CONTROLS"]: raise BadRequest("Invalid Time Control")

    # Loop over the game pool, if a game with a similar rating is in the pool, start the game
    pool : list[OutgoingGames] = OutgoingGames.query.filter_by(mode=mode, time_control=time_control, is_pool=True).order_by(OutgoingGames.created_at).all()
    for outgoing in pool:
        opponent : User = outgoing.user
        if not opponent or \
                (opponent.auth_method == AuthMethods.GUEST and not user.auth_method == AuthMethods.GUEST): continue
        
        if abs(opponent.rating.elo - user.rating.elo) <= CONFIG["ACCEPTABLE_RATING_DIFFERENCE"]:
            # Start the game
            game_id = Game.start_game(user, opponent, mode=mode, time_control=time_control)
            db.session.delete(outgoing)
            db.session.commit()

            # Return the game id to both players
            emit("game_started", {"game_id": game_id}, room=opponent.sid, namespace="/")
            return game_id
    
    # If a valid game was not found, add a new game to the pool
    db.session.add(OutgoingGames(inviter=user, mode=mode, time_control=time_control, is_pool=True))
    db.session.commit()
    return "Added to the pool", 200

@game.route("/invite", methods=["POST"])
@requires_args(Argument("recipient_id", type=str, required=True), Argument("mode", type=str, required=True), Argument("time_control", type=int, required=True))
@requires_auth()
def invite(user : User, args):
    if user.outgoing_game: raise Conflict("You already have an outgoing game")

    opponent : User = User.query.filter_by(user_id=args.recipient_id).first()
    if not opponent: raise NotFound("Opponent Not Found")
    elif opponent == user: raise BadRequest("You cannot invite yourself")

    # Check if the mode and the time control are valid
    mode : str = args.mode
    time_control : int = args.time_control
    if not mode in CONFIG["MODES"]: raise BadRequest("Invalid Mode")
    if not time_control in CONFIG["TIME_CONTROLS"]: raise BadRequest("Invalid Time Control")

    db.session.add(OutgoingGames(inviter=user, recipient=opponent, mode=mode, time_control=time_control))
    db.session.commit()

    emit("incoming_game", {"inviter_id": user.user_id}, room=opponent.sid, namespace="/")
    return "Invite Sent", 200

@game.route("/accept", methods=["POST"])
@requires_args(Argument("inviter_id", type=str, required=True))
@requires_auth()
def accept_invite(user : User, args):
    inviter : User = User.query.filter_by(user_id=args.inviter_id).first()
    if not inviter or inviter.outgoing_game.recipient != user: raise BadRequest("User Not Invited")
    
    game_id = Game.start_game(user, inviter, mode=inviter.outgoing_game.mode, time_control=inviter.outgoing_game.time_control)
    db.session.delete(inviter.outgoing_game)
    db.session.commit()

    emit("game_started", {"game_id": game_id}, room=inviter.sid, namespace="/")
    return game_id

@game.route("/cancel", methods=["POST"])
@requires_auth()
def cancel_outgoing(user : User):
    if not user.outgoing_game: raise NotFound("No Outgoing Games")

    db.session.delete(user.outgoing_game)
    db.session.commit()
    return "Request Deleted", 200