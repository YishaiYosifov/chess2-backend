from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.constants import enums


class GameResults(BaseModel):
    token: Annotated[str, Field(max_length=8)]

    variant: enums.Variant
    time_control: int
    increment: int

    created_at: datetime


class Rating(BaseModel):
    elo: int
    achieved_at: datetime
