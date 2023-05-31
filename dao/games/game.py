from __future__ import annotations
from typing import TYPE_CHECKING

import random
import uuid
import time

if TYPE_CHECKING: from game_modes import Anarchy
from extensions import BOARD, PIECE_DATA
from .game_settings import GameSettings
from .player import Player
from app import db

class Game(db.Model):
    def __init__(self, **data):
        super().__init__(**data)
        self.turn = self.white
        self.white.clock = self.black.clock = time.time() + self.game_settings.time_control

    __tablename__ = "games"

    game_id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text)

    match_id = db.Column(db.Integer, db.ForeignKey("matches.match_id"))
    
    white_id = db.Column(db.Integer, db.ForeignKey("players.player_id"))
    black_id = db.Column(db.Integer, db.ForeignKey("players.player_id"))
    white = db.relationship("Player", backref=db.backref("game_white", uselist=False), foreign_keys=[white_id], uselist=False)
    black = db.relationship("Player", backref=db.backref("game_black", uselist=False), foreign_keys=[black_id], uselist=False)

    game_settings_id = db.Column(db.Integer, db.ForeignKey("game_settings.game_settings_id"))
    game_settings = db.relationship("GameSettings", uselist=False)

    turn_id = db.Column(db.Integer, db.ForeignKey("players.player_id"))
    turn = db.relationship("Player", foreign_keys=[turn_id], uselist=False)

    moves = db.Column(db.PickleType, default=[])
    board = db.Column(db.PickleType, default=BOARD)
    legal_move_cache = db.Column(db.PickleType, default={})

    created_at = db.Column(db.DateTime, server_default=db.text("(UTC_TIMESTAMP)"))
    ended_at = db.Column(db.Double)
    
    is_over = db.Column(db.Boolean, server_default=db.text("FALSE"))

    def get_game_class(self) -> Anarchy:
        import game_modes

        modes = {
            "anarchy": game_modes.Anarchy
        }
        return modes[self.game_settings.mode](self)

    def get_legal_moves(self, origin) -> list:
        cache_origin = tuple(origin.values())
        if cache_origin in self.legal_move_cache: return self.legal_move_cache[cache_origin]

        square = self.board[origin["y"], origin["x"]]
        legal_moves = PIECE_DATA[square.piece.name]["all_legal"](self, origin)
        self.legal_move_cache[cache_origin] = legal_moves
        db.session.query(Game).filter_by(game_id=self.game_id).update({"legal_move_cache": self.legal_move_cache})
        
        return legal_moves

    @classmethod
    def start_game(cls, *players, settings : GameSettings) -> int:
        """
        Start a game

        :param *players: the players
        :param mode: the game mode
        :param time_control: the time control of the game

        :returns game_id: the id of the started game
        """

        # Check if the color the players were in the last game is the same
        if players[0].last_color == players[1].last_color:
            # If it is, randomize who gets each color
            
            players = list(players)
            random.shuffle(players)
            white, black = players
        else:
            # If it's not, give each player the opposite color they were in the last game
            if players[0].last_color == "black": white, black = players
            else: black, white = players
        
        # Update the last color for each user
        white.last_color = "white"
        black.last_color = "black"

        # Insert the game into the active games dict
        token = uuid.uuid4().hex[:8]

        white_player = Player(user=white, color="white")
        black_player = Player(user=black, color="black")
        game = cls(token=token, white=white_player, black=black_player, game_settings=settings)
        db.session.add_all([white_player, black_player, game])

        return token