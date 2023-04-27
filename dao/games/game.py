from datetime import datetime
from typing import Literal

import random
import uuid

from ..database_model import DatabaseModel
from ..members.member import Member

class Game(DatabaseModel):
    def __init__(self, **data):
        super().__init__(**data)

    __tablename__ = "games"
    __primary__ = "game_id"

    game_id : int = None
    token : str
    
    white : Member | int
    black : Member | int
    winner : Literal["white"] | Literal["black"] = None

    mode : str
    time_control : int

    moves : str = ""
    white_wins : int = 0
    black_wins : int = 0

    is_over : bool = False
    created_at : datetime = "CURRENT_TIMESTAMP"

    def to_dict(self, exclude = []) -> dict[str: any]:
        results = super().to_dict(exclude=exclude)
        #results["white"] = results["white"].member_id
        #results["black"] = results["black"].member_id

        return results

    @classmethod
    def start_game(cls, *players : Member, mode : str, time_control : int) -> int:
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
            if players[0].member.last_color == "black": white, black = players
            else: black, white = players
        
        # Update the last color for each user
        white.last_color = "white"
        black.last_color = "black"
        white.update()
        black.update()

        # Insert the game into the active games dict
        token = uuid.uuid4().hex[:8]
        cls(token=token, white=white, black=black, mode=mode, time_control=time_control).insert()
        return token