import re

from .enums import Pieces, Colors

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
    {"piece": Pieces.ROOK, "color": Colors.WHITE, "index": 0},
    {"piece": Pieces.HORSE, "color": Colors.WHITE, "index": 1},
    {"piece": Pieces.KNOOK, "color": Colors.WHITE, "index": 2},
    {"piece": Pieces.XOOK, "color": Colors.WHITE, "index": 3},
    {"piece": Pieces.QUEEN, "color": Colors.WHITE, "index": 4},
    {"piece": Pieces.KING, "color": Colors.WHITE, "index": 5},
    {"piece": Pieces.BISHOP, "color": Colors.WHITE, "index": 6},
    {"piece": Pieces.ANTIQUEEN, "color": Colors.WHITE, "index": 7},
    {"piece": Pieces.HORSE, "color": Colors.WHITE, "index": 8},
    {"piece": Pieces.ROOK, "color": Colors.WHITE, "index": 9},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.WHITE, "index": 10},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.WHITE, "index": 11},
    {"piece": Pieces.PAWN, "color": Colors.WHITE, "index": 12},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.WHITE, "index": 13},
    {"piece": Pieces.PAWN, "color": Colors.WHITE, "index": 14},
    {"piece": Pieces.PAWN, "color": Colors.WHITE, "index": 15},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.WHITE, "index": 16},
    {"piece": Pieces.PAWN, "color": Colors.WHITE, "index": 17},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.WHITE, "index": 18},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.WHITE, "index": 19},
    {"piece": Pieces.ARCHBISHOP, "color": Colors.WHITE, "index": 20},
    {"piece": Pieces.ARCHBISHOP, "color": Colors.BLACK, "index": 29},
    {"piece": Pieces.ARCHBISHOP, "color": Colors.BLACK, "index": 70},
    {"piece": Pieces.ARCHBISHOP, "color": Colors.BLACK, "index": 79},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.BLACK, "index": 80},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.BLACK, "index": 81},
    {"piece": Pieces.PAWN, "color": Colors.BLACK, "index": 82},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.BLACK, "index": 83},
    {"piece": Pieces.PAWN, "color": Colors.BLACK, "index": 84},
    {"piece": Pieces.PAWN, "color": Colors.BLACK, "index": 85},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.BLACK, "index": 86},
    {"piece": Pieces.PAWN, "color": Colors.BLACK, "index": 87},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.BLACK, "index": 88},
    {"piece": Pieces.CHILD_PAWN, "color": Colors.BLACK, "index": 89},
    {"piece": Pieces.ROOK, "color": Colors.BLACK, "index": 90},
    {"piece": Pieces.HORSE, "color": Colors.BLACK, "index": 91},
    {"piece": Pieces.KNOOK, "color": Colors.BLACK, "index": 92},
    {"piece": Pieces.XOOK, "color": Colors.BLACK, "index": 93},
    {"piece": Pieces.QUEEN, "color": Colors.BLACK, "index": 94},
    {"piece": Pieces.KING, "color": Colors.BLACK, "index": 95},
    {"piece": Pieces.BISHOP, "color": Colors.BLACK, "index": 96},
    {"piece": Pieces.ANTIQUEEN, "color": Colors.BLACK, "index": 97},
    {"piece": Pieces.HORSE, "color": Colors.BLACK, "index": 98},
    {"piece": Pieces.ROOK, "color": Colors.BLACK, "index": 99},
]
