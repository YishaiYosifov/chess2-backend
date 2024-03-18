from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas import user_schema
from app.types import StrPoint
from app import enums


class FinishedGame(BaseModel):
    token: str

    user_white: user_schema.UnauthedProfileOut | None
    user_black: user_schema.UnauthedProfileOut | None
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


class Player(BaseModel):
    player_id: int
    user: user_schema.UnauthedProfileOut
    color: enums.Color
    time_remaining: float


class LiveGame(BaseModel):
    token: str

    player_white: Player
    player_black: Player
    turn_player_id: int

    fen: str


class Move(BaseModel):
    notation_type: Annotated[
        enums.NotationType,
        Field(exclude=True),
    ] = enums.NotationType.REGULAR

    is_capture: bool = False
    side_effect_captures: list[StrPoint] = []
    side_effect_moves: dict[StrPoint, StrPoint] = {}


class LegalMoves(BaseModel):
    legal_moves: dict[StrPoint, list[StrPoint]]


class MoveMade(LegalMoves):
    notation: str

    moved: dict[StrPoint, StrPoint]
    captured: list[StrPoint]
