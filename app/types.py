from __future__ import annotations

from operator import add
from typing import NamedTuple, Annotated
import json

from pydantic_core import PydanticCustomError
from pydantic import Field

from app.models.games import game_piece_model

with open("assets/data/countries_alpha3.json", "r") as f:
    COUNTRIES_ALPHA3 = set(json.load(f))


def valid_alpha3(value: str) -> str:
    if value not in COUNTRIES_ALPHA3:
        raise PydanticCustomError(
            "country_alpha3", "Invalid country alpha3 code"
        )
    return value


CountryAlpha3 = Annotated[str, Field(pattern=r"^[A-Z]{3}$"), valid_alpha3]


class Point(NamedTuple("Point", [("x", int), ("y", int)])):
    def __add__(self, other: Point) -> Point:
        return Point(*map(add, self, other))


Board = dict[Point, game_piece_model.GamePiece]
