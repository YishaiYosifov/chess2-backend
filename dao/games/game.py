import random
import uuid

from ..users.user import User
from app import db

class Game(db.Model):
    def __init__(self, **data):
        super().__init__(**data)

    __tablename__ = "games"

    game_id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text)
    
    white_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    black_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))

    white = db.relationship("User", foreign_keys=[white_id], uselist=False)
    black = db.relationship("User", foreign_keys=[black_id], uselist=False)

    winner = db.Column(db.String(10))

    game_settings_id = db.Column(db.Integer, db.ForeignKey("game_settings.game_settings_id"))
    game_settings = db.relationship("GameSettings", uselist=False)

    moves = db.Column(db.Text, server_default=db.text("('')"))
    white_wins = db.Column(db.Integer, server_default=db.text("0"))
    black_wins = db.Column(db.Integer, server_default=db.text("0"))

    is_over = db.Column(db.Boolean, server_default=db.text("FALSE"))
    created_at = db.Column(db.DateTime, default=db.text("(UTC_TIMESTAMP)"))

    @classmethod
    def start_game(cls, *players : User, settings) -> int:
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
        db.session.add(cls(token=token, white=white, black=black, game_settings=settings))
        return token