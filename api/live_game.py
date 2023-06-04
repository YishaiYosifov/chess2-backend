from werkzeug.exceptions import BadRequest, NotFound

from flask_restful.reqparse import Argument
from flask import Blueprint, jsonify

from util import requires_args, requires_auth, column_to_dict
from dao import Game, User
from app import db

live_game = Blueprint("live_game", __name__, url_prefix="/live")

@live_game.route("/sync_clock", methods=["POST"])
@requires_auth(allow_guests=True)
def alert_timeout(user : User):
    if not user.active_game: raise NotFound("No Active Game")
    game_class = user.active_game.get_game_class()
    game_class.sync_clock()
    
    return "Synced", 200

@live_game.route("/get_game", methods=["POST"])
@requires_args(Argument("game_token", type=str, required=True))
def get_board(args):
    game : Game = Game.query.filter_by(token=args.game_token).first()
    if not game: raise NotFound("Game Not Found")

    game_dict = column_to_dict(game, include=["moves", "is_over", "ended_at", "client_legal_move_cache"])
    if game.match: game_dict["match"] = column_to_dict(game, include=["white_score", "black_score"])
    else: game_dict["match"] = {"white_score": 0, "black_score": 0}
    return jsonify(game_dict | {
        "white": column_to_dict(game.white, exclude=["player_id", "turn_ended_at"]),
        "black": column_to_dict(game.black, exclude=["player_id", "turn_ended_at"]),
        "turn": game.turn.user_id,
        "board": [[square.to_dict() for square in row] for row in game.board],
        "mode": game.game_settings.mode,
    }), 200