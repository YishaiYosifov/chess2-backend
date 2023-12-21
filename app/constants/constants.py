from app.schemas import game_schema

from . import enums

BOARD_WIDTH = 10
BOARD_HEIGHT = 10

# fmt: off
MAILBOX = [
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, -1,
    -1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, -1,
    -1, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, -1,
    -1, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, -1,
    -1, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, -1,
    -1, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, -1,
    -1, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, -1,
    -1, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, -1,
    -1, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, -1,
    -1, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
]

MAILBOX_INDICES = [
   25,  26,  27,  28,  29,  30,  31,  32,  33,  34,
   37,  38,  39,  40,  41,  42,  43,  44,  45,  46,
   49,  50,  51,  52,  53,  54,  55,  56,  57,  58,
   61,  62,  63,  64,  65,  66,  67,  68,  69,  70,
   73,  74,  75,  76,  77,  78,  79,  80,  81,  82,
   85,  86,  87,  88,  89,  90,  91,  92,  93,  94,
   97,  98,  99,  100, 101, 102, 103, 104, 105, 106,
   109, 110, 111, 112, 113, 114, 115, 116, 117, 118,
   121, 122, 123, 124, 125, 126, 127, 128, 129, 130,
   133, 134, 135, 136, 137, 138, 139, 140, 141, 142,
]
# fmt: on

# fmt: off
STARTING_POSITION: list[game_schema.Piece] = [
    game_schema.Piece(piece=enums.Piece.ROOK, color=enums.Color.WHITE, index=0),
    game_schema.Piece(piece=enums.Piece.HORSE, color=enums.Color.WHITE, index=1),
    game_schema.Piece(piece=enums.Piece.KNOOK, color=enums.Color.WHITE, index=2),
    game_schema.Piece(piece=enums.Piece.XOOK, color=enums.Color.WHITE, index=3),
    game_schema.Piece(piece=enums.Piece.QUEEN, color=enums.Color.WHITE, index=4),
    game_schema.Piece(piece=enums.Piece.KING, color=enums.Color.WHITE, index=5),
    game_schema.Piece(piece=enums.Piece.BISHOP, color=enums.Color.WHITE, index=6),
    game_schema.Piece(piece=enums.Piece.ANTIQUEEN, color=enums.Color.WHITE, index=7),
    game_schema.Piece(piece=enums.Piece.HORSE, color=enums.Color.WHITE, index=8),
    game_schema.Piece(piece=enums.Piece.ROOK, color=enums.Color.WHITE, index=9),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, index=10),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, index=11),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.WHITE, index=12),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, index=13),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.WHITE, index=14),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.WHITE, index=15),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, index=16),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.WHITE, index=17),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, index=18),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, index=19),
    game_schema.Piece(piece=enums.Piece.ARCHBISHOP, color=enums.Color.WHITE, index=20),
    game_schema.Piece(piece=enums.Piece.ARCHBISHOP, color=enums.Color.WHITE, index=29),
    game_schema.Piece(piece=enums.Piece.ARCHBISHOP, color=enums.Color.BLACK, index=70),
    game_schema.Piece(piece=enums.Piece.ARCHBISHOP, color=enums.Color.BLACK, index=79),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, index=80),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, index=81),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.BLACK, index=82),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, index=83),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.BLACK, index=84),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.BLACK, index=85),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, index=86),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.BLACK, index=87),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, index=88),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, index=89),
    game_schema.Piece(piece=enums.Piece.ROOK, color=enums.Color.BLACK, index=90),
    game_schema.Piece(piece=enums.Piece.HORSE, color=enums.Color.BLACK, index=91),
    game_schema.Piece(piece=enums.Piece.ANTIQUEEN, color=enums.Color.BLACK, index=92),
    game_schema.Piece(piece=enums.Piece.BISHOP, color=enums.Color.BLACK, index=93),
    game_schema.Piece(piece=enums.Piece.KING, color=enums.Color.BLACK, index=94),
    game_schema.Piece(piece=enums.Piece.QUEEN, color=enums.Color.BLACK, index=95),
    game_schema.Piece(piece=enums.Piece.XOOK, color=enums.Color.BLACK, index=96),
    game_schema.Piece(piece=enums.Piece.KNOOK, color=enums.Color.BLACK, index=97),
    game_schema.Piece(piece=enums.Piece.HORSE, color=enums.Color.BLACK, index=98),
    game_schema.Piece(piece=enums.Piece.ROOK, color=enums.Color.BLACK, index=99),
]

# fmt: on
