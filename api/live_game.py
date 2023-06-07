from flask_restful.reqparse import Argument
from werkzeug.exceptions import NotFound
from flask import Blueprint, jsonify

from util import requires_args, requires_auth, column_to_dict
from dao import User, Game
from app import db

live_game = Blueprint("live_game", __name__, url_prefix="/live")

@live_game.route("/sync_clock", methods=["POST"])
@requires_auth(allow_guests=True)
def sync_clock(user : User):
    if not user.active_game: raise NotFound("No Active Game")
    user.active_game.get_game_class().sync_clock()
    
    return "Synced", 200

@live_game.route("/alert_stalling", methods=["POST"])
@requires_args(Argument("user_id", type=int, required=True))
@requires_auth(allow_guests=True)
def alert_stalling(user : User, args):
    if not user.active_game: raise NotFound("No Active Game")

    stalling_user : User = User.query.filter_by(user_id=args.user_id).first()
    if not stalling_user or not (
                stalling_user == user.active_game.white or \
                stalling_user == user.active_game.black
            ): raise NotFound("User Not Found")
    user.active_game.get_game_class().alert_stalling(stalling_user)

    return "Stalling Alerted", 200

@live_game.route("/load_game", methods=["POST"])
@requires_args(Argument("game_token", type=str))
@requires_auth(allow_guests=True)
def get_board(user : User, args):
    if user.active_game:
        if user.active_game.token == args.game_token:
            game = Game.query.filter_by(token=args.game_token).first()
            if not game: raise NotFound("No Active Game")
        else: game = user.active_game
        game.get_game_class()._get_player(user).is_loading = True
        db.session.commit()
    else:
        game = Game.query.filter_by(token=args.game_token).first()
        if not game: raise NotFound("No Active Game")

    game_dict = column_to_dict(game, include=["moves", "is_over", "ended_at", "client_legal_move_cache"])
    if game.match: game_dict["match"] = column_to_dict(game, include=["white_score", "black_score"])
    else: game_dict["match"] = {"white_score": 0, "black_score": 0}
    return jsonify(game_dict | {
        "white": column_to_dict(game.white, exclude=["player_id"]),
        "black": column_to_dict(game.black, exclude=["player_id"]),
        "turn": game.turn.user_id,
        "board": [[square.to_dict() for square in row] for row in game.board],
        "game_settings": column_to_dict(game.game_settings, exclude=["game_settings_id"]),
    }), 200