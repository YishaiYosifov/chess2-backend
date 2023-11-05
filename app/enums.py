from __future__ import annotations

from enum import Enum


class AuthMethods(Enum):
    CREDENTIALS = "credentials"
    EMAIL = "gmail"
    GUEST = "guest"


class Variants(Enum):
    FOG_OF_WAR = "fog of war"
    ANARCHY = "anarchy"
    CHSS = "chss"


class Colors(Enum):
    WHITE = "white"
    BLACK = "black"

    def invert(self) -> Colors:
        return self.BLACK if self == Colors.WHITE else Colors.WHITE


class Pieces(Enum):
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
