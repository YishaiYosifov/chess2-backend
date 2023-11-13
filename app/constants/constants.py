import re

from .enums import Piece, Color

STALL_TIMEOUTES = {
    "1": 60,
    "3": 90,
    "5": 120,
    "10": 200,
    "15": 210,
    "30": 470,
    "180": 200,
}
FIRST_MOVES_STALL_TIMEOUT = 25
DISCONNECTION_TIMEOUT = 60
ELO_K_FACTOR = 15

ACCEPTABLE_RATING_DIFFERENCE = 300

STRONG_PASSWORD_REGEX = re.compile(r"^(?=.*[A-Z])(?=.*)(?=.*[0-9])(?=.*[a-z]).{8,}$")

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

STARTING_POSITION = [
    {"piece": Piece.ROOK, "color": Color.WHITE, "index": 0},
    {"piece": Piece.HORSE, "color": Color.WHITE, "index": 1},
    {"piece": Piece.KNOOK, "color": Color.WHITE, "index": 2},
    {"piece": Piece.XOOK, "color": Color.WHITE, "index": 3},
    {"piece": Piece.QUEEN, "color": Color.WHITE, "index": 4},
    {"piece": Piece.KING, "color": Color.WHITE, "index": 5},
    {"piece": Piece.BISHOP, "color": Color.WHITE, "index": 6},
    {"piece": Piece.ANTIQUEEN, "color": Color.WHITE, "index": 7},
    {"piece": Piece.HORSE, "color": Color.WHITE, "index": 8},
    {"piece": Piece.ROOK, "color": Color.WHITE, "index": 9},
    {"piece": Piece.CHILD_PAWN, "color": Color.WHITE, "index": 10},
    {"piece": Piece.CHILD_PAWN, "color": Color.WHITE, "index": 11},
    {"piece": Piece.PAWN, "color": Color.WHITE, "index": 12},
    {"piece": Piece.CHILD_PAWN, "color": Color.WHITE, "index": 13},
    {"piece": Piece.PAWN, "color": Color.WHITE, "index": 14},
    {"piece": Piece.PAWN, "color": Color.WHITE, "index": 15},
    {"piece": Piece.CHILD_PAWN, "color": Color.WHITE, "index": 16},
    {"piece": Piece.PAWN, "color": Color.WHITE, "index": 17},
    {"piece": Piece.CHILD_PAWN, "color": Color.WHITE, "index": 18},
    {"piece": Piece.CHILD_PAWN, "color": Color.WHITE, "index": 19},
    {"piece": Piece.ARCHBISHOP, "color": Color.WHITE, "index": 20},
    {"piece": Piece.ARCHBISHOP, "color": Color.BLACK, "index": 29},
    {"piece": Piece.ARCHBISHOP, "color": Color.BLACK, "index": 70},
    {"piece": Piece.ARCHBISHOP, "color": Color.BLACK, "index": 79},
    {"piece": Piece.CHILD_PAWN, "color": Color.BLACK, "index": 80},
    {"piece": Piece.CHILD_PAWN, "color": Color.BLACK, "index": 81},
    {"piece": Piece.PAWN, "color": Color.BLACK, "index": 82},
    {"piece": Piece.CHILD_PAWN, "color": Color.BLACK, "index": 83},
    {"piece": Piece.PAWN, "color": Color.BLACK, "index": 84},
    {"piece": Piece.PAWN, "color": Color.BLACK, "index": 85},
    {"piece": Piece.CHILD_PAWN, "color": Color.BLACK, "index": 86},
    {"piece": Piece.PAWN, "color": Color.BLACK, "index": 87},
    {"piece": Piece.CHILD_PAWN, "color": Color.BLACK, "index": 88},
    {"piece": Piece.CHILD_PAWN, "color": Color.BLACK, "index": 89},
    {"piece": Piece.ROOK, "color": Color.BLACK, "index": 90},
    {"piece": Piece.HORSE, "color": Color.BLACK, "index": 91},
    {"piece": Piece.KNOOK, "color": Color.BLACK, "index": 92},
    {"piece": Piece.XOOK, "color": Color.BLACK, "index": 93},
    {"piece": Piece.QUEEN, "color": Color.BLACK, "index": 94},
    {"piece": Piece.KING, "color": Color.BLACK, "index": 95},
    {"piece": Piece.BISHOP, "color": Color.BLACK, "index": 96},
    {"piece": Piece.ANTIQUEEN, "color": Color.BLACK, "index": 97},
    {"piece": Piece.HORSE, "color": Color.BLACK, "index": 98},
    {"piece": Piece.ROOK, "color": Color.BLACK, "index": 99},
]
