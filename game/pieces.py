import math

import numpy

from dao import Piece

# Collisions
def straight_collision(board, origin : dict, destination : dict) -> numpy.ndarray:
    x1, x2 = min(origin["x"], destination["x"]), max(origin["x"], destination["x"])
    y1, y2 = min(origin["y"], destination["y"]), max(origin["y"], destination["y"])

    if x1 == x2: return board[y1 + 1:y2 + 1, x1]
    else: return board[y1, x1 + 1:x2 + 1]
def diagonal_collision(board, origin : dict, destination : dict) -> numpy.ndarray:
    x1, y1 = origin.values()
    x2, y2 = destination.values()

    diagonal = board[min(y1, y2):max(y1, y2) + 1, min(x1, x2):max(x1, x2) + 1]
    if (x1 > x2 and y1 < y2) or (y1 > y2 and x1 < x2): diagonal = numpy.flipud(diagonal)
    diagonal = diagonal.diagonal()

    diagonal = diagonal[diagonal != board[origin["y"], origin["x"]]]
    return diagonal

# Piece movement
straight_movement = lambda _, origin, destination: origin["x"] == destination["x"] or origin["y"] == destination["y"]
diagonal_movement = lambda _, origin, destination: abs(origin["x"] - destination["x"]) == abs(origin["y"] - destination["y"])
horse_movement = lambda _, origin, destination: (abs(origin["y"] - destination["y"]) == 2 and abs(origin["x"] - destination["x"]) == 1) or \
                                                (abs(origin["y"] - destination["y"]) == 1 and abs(origin["x"] - destination["x"]) == 2)

def pawn_movement(board : numpy.ndarray, origin : dict, destination : dict) -> bool:
    piece : Piece = board[origin["y"], origin["x"]]
    if piece.moved == 0:
        board_width = len(board[0])
        if (board_width % 2 == 0 and \
                (origin["x"] == (board_width / 2) - 1 or \
                 origin["x"] == board_width / 2)) or \
            (board_width % 2 != 0 and origin["x"] == math.floor(board_width / 2)): limit = 3
        else: limit = 2
    else: limit = 1

    return origin["x"] == destination["x"] and abs(destination["y"] - origin["y"]) <= limit

PIECE_MOVEMENT = {
    "rook": {
        "move": {
            "validator": straight_movement,
            "collisions": [straight_collision]
        },
    },
    "bishop": {
        "move": {
            "validator": diagonal_movement,
            "collisions": [diagonal_collision]
        }
    },
    "horse": {
        "move": {
            "validator": horse_movement
        }
    },
    "king": {
        "move": {
            "validator": lambda _, origin, destination: abs(origin["y"] - destination["y"]) <= 1 and abs(origin["x"] - destination["x"]) <= 1,
            "collisions": [straight_collision, diagonal_collision]
        }
    },
    "queen": {
        "move": {
            "validator": lambda board, origin, destination: straight_movement(board, origin, destination) or diagonal_movement(board, origin, destination),
            "collisions": [straight_collision, diagonal_collision]
        }
    },
    "antiqueen": {
        "move": {
            "validator": horse_movement,
        }
    },
    "xook": {
        "move": {
            "validator": diagonal_movement,
            "collisions": [diagonal_collision]
        }
    },
    "knook": {
        "move": {
            "validator": horse_movement
        },
        "capture": {
            "validator": straight_movement,
            "collisions": [straight_collision]
        }
    },
    "pawn": {
        "move": {
            "validator": lambda board, origin, destination: pawn_movement(board, origin, destination),
            "collisions": [straight_collision]
        },
        "capture": {
            "validator": lambda _, origin, destination: abs(origin["y"] - destination["y"]) == 1 and origin["x"] != destination["x"]
        },
    },
    "child-pawn": {
        "move": {
            "validator": lambda board, origin, destination: pawn_movement(board, origin, destination),
            "collisions": [straight_collision]
        },
        "capture": {
            "validator": lambda _, origin, destination: abs(origin["y"] - destination["y"]) == 1 and origin["x"] != destination["x"]
        },
    },
    "archbishop": {
        "move": {
            "validator": lambda _, origin, destination: (abs(origin["x"] - destination["x"]) + abs(origin["y"] - destination["y"])) % 2 == 0,
            "collisions": [straight_collision]
        }
    }
}