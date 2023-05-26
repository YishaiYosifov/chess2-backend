from werkzeug.exceptions import BadRequest, Conflict, NotFound

from flask_restful.reqparse import Argument
from flask import Blueprint, jsonify
from flask_socketio import emit

from dao import GameSettings, OutgoingGames, Game, User, AuthMethods, RatingArchive
from util import requires_args, requires_auth, column_to_dict
from extensions import CONFIG
from app import db

game = Blueprint("game", __name__, url_prefix="/game")

@game.route("/pool/start", methods=["POST"])
@requires_args(Argument("mode", type=str, required=True), Argument("time_control", type=int, required=True), Argument("increment", type=int, required=True))
@requires_auth(allow_guests=True)
def start_pool_game(user : User, args):
    """
    Start a game with a random
    """

    if user.outgoing_game: raise Conflict("You already have an outgoing game")
    elif user.get_active_game(): raise Conflict("You already have an active game")

    # Check if the mode and the time control are valid
    mode : str = args.mode.lower()
    time_control : int = args.time_control
    increment : int = args.increment
    if not mode in CONFIG["MODES"]: raise BadRequest("Invalid Mode")
    if not time_control in CONFIG["TIME_CONTROLS"]: raise BadRequest("Invalid Time Control")
    if not increment in CONFIG["INCREMENTS"]: raise BadRequest("Invalid Increment")
    time_control *= 60

    rating : RatingArchive = user.rating(mode)

    # Loop over the game pool, if a game with a similar rating is in the pool, start the game
    pool : list[OutgoingGames] = OutgoingGames.query.filter_by(is_pool=True).order_by(OutgoingGames.created_at).join(GameSettings).filter_by(mode=mode, time_control=time_control, increment=increment).all()
    for outgoing in pool:
        opponent : User = outgoing.inviter
        if not opponent or \
                (opponent.auth_method == AuthMethods.GUEST and not user.auth_method == AuthMethods.GUEST): continue
        
        if abs(opponent.rating(mode).elo - rating.elo) <= CONFIG["ACCEPTABLE_RATING_DIFFERENCE"]:
            # Start the game
            game_id = Game.start_game(user, opponent, settings=outgoing.game_settings)
            db.session.delete(outgoing)
            db.session.commit()

            # Return the game id to both players
            emit("game_started", {"game_id": game_id}, room=opponent.sid, namespace="/")
            return game_id
    
    # If a valid game was not found, add a new game to the pool
    game_settings = GameSettings(mode=mode, time_control=time_control, increment=increment)
    db.session.add_all([game_settings, OutgoingGames(inviter=user, game_settings=game_settings, is_pool=True)])
    db.session.commit()
    return "Added to the pool", 201

@game.route("/invite", methods=["POST"])
@requires_args(Argument("recipient_id", type=str, required=True), Argument("mode", type=str, required=True), Argument("time_control", type=int, required=True), Argument("increment", type=int, required=True))
@requires_auth()
def invite(user : User, args):
    if user.outgoing_game: raise Conflict("You already have an outgoing game")
    elif user.get_active_game(): raise Conflict("You already have an active game")

    opponent : User = User.query.filter_by(user_id=args.recipient_id).first()
    if not opponent: raise NotFound("Opponent Not Found")
    elif opponent == user: raise BadRequest("You cannot invite yourself")

    # Check if the mode and the time control are valid
    mode : str = args.mode
    time_control : int = args.time_control
    increment : int = args.increment
    if not mode in CONFIG["MODES"]: raise BadRequest("Invalid Mode")
    if not time_control in CONFIG["TIME_CONTROLS"]: raise BadRequest("Invalid Time Control")
    if not increment in CONFIG["INCREMENTS"]: raise BadRequest("Invalid Increment")

    game_settings = GameSettings(mode=mode, time_control=time_control * 60, increment=increment)
    db.session.add_all([game_settings, OutgoingGames(inviter=user, recipient=opponent, game_settings=game_settings)])
    db.session.commit()

    emit("incoming_games", [user.user_id], room=opponent.sid, namespace="/")
    return "Invite Sent", 200

@game.route("/accept", methods=["POST"])
@requires_args(Argument("inviter_id", type=str, required=True))
@requires_auth()
def accept_invite(user : User, args):
    inviter : User = User.query.filter_by(user_id=args.inviter_id).first()
    if not inviter or inviter.outgoing_game.recipient != user: raise BadRequest("User Not Invited")
    elif user.get_active_game(): raise Conflict("You already have an active game")
    
    game_id = Game.start_game(user, inviter, settings=inviter.outgoing_game.game_settings)
    db.session.delete(inviter.outgoing_game)
    db.session.commit()

    emit("game_started", {"game_id": game_id}, room=inviter.sid, namespace="/")
    return game_id, 200

@game.route("/cancel", methods=["POST"])
@requires_auth(allow_guests=True)
def cancel_outgoing(user : User):
    if not user.outgoing_game: raise NotFound("No Outgoing Games")

    db.session.delete(user.outgoing_game)
    db.session.delete(user.outgoing_game.game_settings)
    db.session.commit()
    return "Request Deleted", 200

@game.route("/has_outgoing", methods=["POST"])
@requires_auth(allow_guests=True)
def has_outgoing(user : User): return jsonify(user.outgoing_game != None)

@game.route("/get_game", methods=["POST"])
@requires_args(Argument("game_token", type=str, required=True))
def get_board(args):
    game : Game = Game.query.filter_by(token=args.game_token).first()
    if not game: raise NotFound("Game Not Found")

    game_dict = column_to_dict(game, include=["moves", "is_over"])
    if game.match: game_dict["match"] = column_to_dict(game, include=["white_score", "black_score"])
    else: game_dict["match"] = {"white_score": 0, "black_score": 0}
    return jsonify(game_dict | {
        "white": game.white.user_id,
        "black": game.black.user_id,
        "turn": game.turn.user_id,
        "board": [[square.to_dict() for square in row] for row in game.board],
        "mode": game.game_settings.mode
    }), 200

@game.route("/get_legal", methods=["POST"])
@requires_args(Argument("game_token", type=str, required=True), Argument("x", type=int, required=True), Argument("y", type=int, required=True))
def get_legal_moves(args):
    game : Game = Game.query.filter_by(token=args.game_token).first()
    if not game: raise NotFound("Game Not Found")

    try: square = game.board[args.y, args.x]
    except IndexError: raise BadRequest("Invalid Square")
    if not square.piece: raise BadRequest("Invalid Square")

    legal_moves = game.get_legal_moves({"x": args.x, "y": args.y})
    db.session.commit()
    return jsonify(
        list(
            map(lambda move: {"x": move.x, "y": move.y}, legal_moves)
        )), 200