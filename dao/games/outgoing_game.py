from datetime import datetime

from ..database_model import DatabaseModel

class OutgoingGame(DatabaseModel):
    __tablename__ = "outgoing_games"
    __primary__ = "outgoing_game_id"

    outgoing_game_id : int = None
    from_id : int

    rating : int
    mode : str
    time_control : int

    created_at : datetime = "CURRENT_TIMESTAMP"
    is_pool : bool = False