from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.constants import enums
from app.schemas import user_schema


class GameResults(BaseModel):
    token: Annotated[str, Field(max_length=8)]

    user_white: user_schema.SimpleUserOut | None
    user_black: user_schema.SimpleUserOut | None
    results: enums.GameResult
    variant: enums.Variant
    time_control: int
    increment: int

    created_at: datetime


class Rating(BaseModel):
    elo: int
    achieved_at: datetime


class RatingOverview(BaseModel):
    min: int
    max: int
    current: int

    history: list[Rating]


class GameSettings(BaseModel):
    variant: enums.Variant
    time_control: int
    increment: int


class GameRequest(GameSettings):
    test: int


class Piece(BaseModel):
    piece: enums.Piece
    color: enums.Color

    index: int
