from typing import NamedTuple, Annotated
import json

from pydantic_core import core_schema, PydanticCustomError
from pydantic import GetPydanticSchema, PlainSerializer, Field

from app import enums

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
    can_capture: bool = True


class Point(NamedTuple):
    x: int
    y: int

    def __add__(self, other: "Point | Offset") -> "Point":
        return Point(self.x + other.x, self.y + other.y)


StrPoint = Annotated[
    Point,
    PlainSerializer(
        lambda point: f"{point.x},{point.y}",
        return_type=str,
        when_used="json",
    ),
    # parse string tuple into a list for validation.
    # for example if "1,2" is provided, ["1", "2"] would be returned
    # and pydantic will turn it into a Point object
    GetPydanticSchema(
        lambda tp, handler: core_schema.no_info_before_validator_function(
            lambda x: x.split(",") if isinstance(x, str) else x,
            handler(tp),
        )
    ),
]


class PieceInfo(NamedTuple):
    piece_type: enums.PieceType
    color: enums.Color
