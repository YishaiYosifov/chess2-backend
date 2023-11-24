from __future__ import annotations

from enum import Enum


class Variant(Enum):
    FOG_OF_WAR = "fog of war"
    ANARCHY = "anarchy"
    CHSS = "chss"


class Color(Enum):
    WHITE = "white"
    BLACK = "black"

    def invert(self) -> Color:
        return self.BLACK if self == Color.WHITE else Color.WHITE


class GameResult(Enum):
    WHITE = "white"
    BLACK = "black"
    DRAW = "draw"


class Piece(Enum):
    KING = "king"
    QUEEN = "queen"
    ROOK = "rook"
    KNOOK = "knook"
    XOOK = "xook"
    ANTIQUEEN = "antiqueen"
    ARCHBISHOP = "archbishop"
    BISHOP = "bishop"
    HORSE = "horse"
    PAWN = "pawn"
    CHILD_PAWN = "child_pawn"
