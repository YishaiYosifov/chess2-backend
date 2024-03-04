from __future__ import annotations

from typing import NamedTuple, Annotated
import json

from pydantic_core import PydanticCustomError
from pydantic import Field

with open("assets/data/countries_alpha3.json", "r") as f:
    COUNTRIES_ALPHA3 = set(json.load(f))


def valid_alpha3(value: str) -> str:
    if value not in COUNTRIES_ALPHA3:
        raise PydanticCustomError(
            "country_alpha3", "Invalid country alpha3 code"
        )
    return value


CountryAlpha3 = Annotated[str, Field(pattern=r"^[A-Z]{3}$"), valid_alpha3]


class Offset(NamedTuple):
    x: int
    y: int

    # should the piece "slide" in this direction until blocked
    # or move just once?
    slide: bool = True


class Point(NamedTuple):
    x: int
    y: int

    def __add__(self, other: Point | Offset) -> Point:
        return Point(self.x + other.x, self.y + other.y)
