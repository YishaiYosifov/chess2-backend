from typing import Literal

from ..database_model import DatabaseModel

class Rating(DatabaseModel):
    __tablename__ = "ratings"
    __primary__ = "rating_id"

    rating_id : int = None
    member_id : int

    mode : Literal["anarchy"] | Literal["chss"] | Literal["fog of war"]
    elo : int = 800