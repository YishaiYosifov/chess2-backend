from enum import Enum


class Variant(Enum):
    FOG_OF_WAR = "fog of war"
    ANARCHY = "anarchy"
    CHSS = "chss"


class Color(Enum):
    WHITE = "white"
    BLACK = "black"

    def invert(self) -> "Color":
        return Color.BLACK if self == Color.WHITE else Color.WHITE


class GameResult(Enum):
    WHITE = "white"
    BLACK = "black"
    DRAW = "draw"


class UserType(Enum):
    AUTHED = "authed"
    GUEST = "guest"


class NotationType(Enum):
    REGULAR = "regular"
    CASTLE = "castle"
    VERTICAL_CASTLE = "vertical_castle"
    IL_VATICANO = "il_vaticano"


class PieceType(Enum):
    KING = "k"
    QUEEN = "q"
    ROOK = "r"
    KNOOK = "n"
    XOOK = "x"
    ANTIQUEEN = "a"
    ARCHBISHOP = "c"
    BISHOP = "b"
    HORSIE = "h"
    PAWN = "p"
    CHILD_PAWN = "d"


class WSEvent(Enum):
    NOTIFICATION = "notification"
    GAME_START = "game_start"
