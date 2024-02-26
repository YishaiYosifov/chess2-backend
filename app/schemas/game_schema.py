from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.constants import enums
from app.schemas import user_schema


class FinishedGame(BaseModel):
    token: str

    user_white: user_schema.PublicUserOut | None
    user_black: user_schema.PublicUserOut | None
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
    time_control: Annotated[int, Field(ge=10)]
    increment: Annotated[int, Field(ge=0)]


class Piece(BaseModel):
    piece_type: enums.PieceType
    color: enums.Color

    x: int
    y: int


class Player(BaseModel):
    user: user_schema.PublicUserOut
    color: enums.Color
    time_remaining: float


class LiveGame(BaseModel):
    token: str

    player_white: Player
    player_black: Player
    turn_player_id: int

    pieces: list[Piece]
