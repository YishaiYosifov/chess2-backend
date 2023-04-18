from typing import Literal

from pydantic import BaseModel

from .database_model import DatabaseModel

class Game(BaseModel, DatabaseModel):
    _table = "games"
    _primary = "game_id"

    game_id : int = None
    
    white_id : int
    black_id : int
    winner : Literal["white"] | Literal["black"]

    timestamp : int
    mode : str

    moves : str
    white_wins : int = 0
    black_wins : int = 0