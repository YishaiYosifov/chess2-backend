import random
import uuid

from extensions import BOARD, PIECE_DATA
from .game_settings import GameSettings
from app import db

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

    moves = db.Column(db.PickleType, default=[])
    board = db.Column(db.PickleType, default=BOARD)
    clocks = db.Column(db.PickleType)
    legal_move_cache = db.Column(db.PickleType, default={})

    created_at = db.Column(db.DateTime, default=db.text("(UTC_TIMESTAMP)"))

    def get_legal_moves(self, origin):
        cache_origin = tuple(origin.values())
        if cache_origin in self.legal_move_cache: return self.legal_move_cache[origin]

        square = self.board[origin["y"], origin["x"]]
        legal_moves = PIECE_DATA[square.piece.name]["all_legal"](self, origin)
        self.legal_move_cache[cache_origin] = legal_moves
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
        game = cls(token=token, white=white, black=black, game_settings=settings)
        db.session.add(game)

        from game_modes import GameBase
        active_games[token] = GameBase(Game.query.filter_by(token=token).first())

        return token