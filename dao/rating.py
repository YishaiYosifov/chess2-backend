from typing import Literal

from pydantic import BaseModel

from .database_model import DatabaseModel

class Rating(BaseModel, DatabaseModel):
    _table = "ratings"
    _primary = "rating_id"

    rating_id : int = None
    member_id : int

    mode : Literal["anarchy"] | Literal["chss"] | Literal["fog of war"]
    rating : int = 800