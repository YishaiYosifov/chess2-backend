from typing import Literal

import random
import numpy
import uuid

from pydantic import BaseModel

from .game_settings import GameSettings
from extensions import CONFIG
from app import db

class Piece(BaseModel):
    name : str
    color : Literal["white"] | Literal["black"]

    moved = False

class Square(BaseModel):
    piece : Piece = None

    x : int
    y : int

    def to_dict(self) -> dict:
        results = self.__dict__.copy()
        if self.piece: results["piece"] = self.piece.__dict__
        return results

# Initilize default board
SET_HEIGHT = len(CONFIG["PIECE_SET"])

parsed_pieces_white = numpy.empty((SET_HEIGHT, 8), Square)
parsed_pieces_black = numpy.empty((SET_HEIGHT, 8), Square)
for row_index, row in enumerate(CONFIG["PIECE_SET"]):
    for column_index, piece in enumerate(row):
        parsed_pieces_white[row_index][column_index] = Square(piece=Piece(name=piece, color="white") if piece else None, x=column_index, y=row_index)
        parsed_pieces_black[row_index][column_index] = Square(piece=Piece(name=piece, color="black") if piece else None, x=column_index, y=(SET_HEIGHT + 4) - row_index + 2)
parsed_pieces_black = parsed_pieces_black[::-1]

BOARD = numpy.concatenate((
    parsed_pieces_white,
    [[Square(x=column_index, y=SET_HEIGHT + row_index) for column_index in range(8)] for row_index in range(4)],
    parsed_pieces_black
))

active_games = {}
class Game(db.Model):
    def __init__(self, **data):
        super().__init__(**data)

        self.turn = self.white
        self.clocks = {
            data["white"].user_id: self.game_settings.time_control,
            data["black"].user_id: self.game_settings.time_control
        }
        db.session.commit()

    __tablename__ = "games"

    game_id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text)
    
    white_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    black_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))

    white = db.relationship("User", foreign_keys=[white_id], uselist=False)
    black = db.relationship("User", foreign_keys=[black_id], uselist=False)

    game_settings_id = db.Column(db.Integer, db.ForeignKey("game_settings.game_settings_id"))
    game_settings = db.relationship("GameSettings", uselist=False)

    turn_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    turn = db.relationship("User", foreign_keys=[turn_id], uselist=False)

    moves = db.Column(db.PickleType, default=[], nullable=False)
    board = db.Column(db.PickleType, default=BOARD, nullable=False)
    clocks = db.Column(db.PickleType)

    created_at = db.Column(db.DateTime, default=db.text("(UTC_TIMESTAMP)"))

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
        game = cls(token=token, white=white, black=black, game_settings=settings)
        db.session.add(game)

        from game import GameBase
        active_games[token] = GameBase(Game.query.filter_by(token=token).first())

        return token