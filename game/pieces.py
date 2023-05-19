import math

import numpy

from dao import Piece, Square, Game

# Forced moves
# @returns
# 0: not forced
# 1: forced, not played
# 2: played
def enpassant_forced_status(game : Game, square : Square, origin : dict, destination : dict) -> int:
    if not game.moves: return 0

    y_offset = 1 if square.piece.color == "white" else -1
    found_move = False
    for x_offset in [-1, 1]:
        if not _can_enpassant(game, square, x_offset): continue
        elif origin["x"] != square.x or origin["y"] != square.y: return 1
        found_move = True
        
        m = ((square.y + y_offset) - square.y) / ((square.x + x_offset) - square.x)
        b = square.y - m * square.x
        expected_y = m * destination["x"] + b
        if expected_y == destination["y"]: return 2
    return 1 if found_move else 0

def bishop_childpawn_forced_status(game : Game, origin : dict, destination : dict) -> bool: pass

# Collisions
def straight_collision(game : Game, origin : dict, destination : dict) -> numpy.ndarray:
    x1, x2 = min(origin["x"], destination["x"]), max(origin["x"], destination["x"])
    y1, y2 = min(origin["y"], destination["y"]), max(origin["y"], destination["y"])

    if x1 == x2:
        if origin["y"] > destination["y"]: return numpy.flip(game.board[y1:y2, x1])
        else: return game.board[y1 + 1:y2 + 1, x1]
    else: return game.board[y1, x1:x2]
def diagonal_collision(game : Game, origin : dict, destination : dict) -> numpy.ndarray:
    x1, y1 = origin.values()
    x2, y2 = destination.values()

    diagonal = game.board[min(y1, y2):max(y1, y2) + 1, min(x1, x2):max(x1, x2) + 1]
    if (x1 > x2 and y1 < y2) or (y1 > y2 and x1 < x2): diagonal = numpy.flipud(diagonal)
    diagonal = diagonal.diagonal()

    diagonal = diagonal[diagonal != game.board[origin["y"], origin["x"]]]
    return diagonal

def pawn_collision(game : Game, origin : dict, destination : dict) -> bool:
    if not diagonal_movement(game, origin, destination): return straight_collision(game, origin, destination)

    if not game.moves: return []
    current_square : Piece = game.board[origin["y"]][origin["x"]]
    current_piece = current_square.piece

    # regular capture
    capture_diagonal = diagonal_collision(game, origin, destination)
    if capture_diagonal[0].piece:
        if len(capture_diagonal) != 1 or not capture_diagonal[0] or current_piece.color == capture_diagonal[0].piece.color: return False
        return numpy.asarray([capture_diagonal[0]])

    # en passant
    if origin["y"] - destination["y"] > 0: x_offset = 1 if current_piece.color == "white" else -1
    elif origin["y"] - destination["y"] < 0: x_offset = -1 if current_piece.color == "white" else 1

    if not _can_enpassant(game, current_square, x_offset): return False

    y_offset = -1 if current_piece.color == "white" else 1

    enpassant_origin = origin.copy()
    enpassant_destination = destination.copy()
    enpassant_origin["y"] += y_offset
    enpassant_destination["y"] += y_offset

    enpassant_diagonal = diagonal_collision(game, enpassant_origin, enpassant_destination)
    for enpassant_square, capture_square in zip(enpassant_diagonal, capture_diagonal):
        if capture_square.piece or \
            not enpassant_square.piece or \
            not "pawn" in enpassant_square.piece.name or \
            enpassant_square.piece.color == current_piece.color: return False
        enpassant_square.piece = None
    game.board[destination["y"], destination["x"]].piece = current_piece
    return True

def _can_enpassant(game : Game, square : Square, side : int) -> bool:
    if not game.moves: return False

    last_move = game.moves[-1]
    try: return "pawn" in last_move["piece"] and \
            game.board[square.y, square.x + side].piece and \
            last_move["destination"] == {"x": square.x + side, "y": square.y} and \
            abs(last_move["destination"]["y"] - last_move["origin"]["y"]) > 1 and \
            last_move["origin"]["x"] == last_move["destination"]["x"]
    except IndexError: return False

        
# Piece movement
straight_movement = lambda game, origin, destination: origin["x"] == destination["x"] or origin["y"] == destination["y"]
diagonal_movement = lambda game, origin, destination: abs(origin["x"] - destination["x"]) == abs(origin["y"] - destination["y"])
horse_movement = lambda game, origin, destination: (abs(origin["y"] - destination["y"]) == 2 and abs(origin["x"] - destination["x"]) == 1) or \
                                                (abs(origin["y"] - destination["y"]) == 1 and abs(origin["x"] - destination["x"]) == 2)

def pawn_movement(game : Game, origin : dict, destination : dict) -> bool:
    piece : Piece = game.board[origin["y"], origin["x"]].piece

    if not piece.moved:
        board_width = len(game.board[0])
        if (board_width % 2 == 0 and \
                (origin["x"] == (board_width / 2) - 1 or \
                 origin["x"] == board_width / 2)) or \
            (board_width % 2 != 0 and origin["x"] == math.floor(board_width / 2)): limit = 3
        else: limit = 2
    else: limit = 1

    return origin["x"] == destination["x"] and abs(destination["y"] - origin["y"]) <= limit

PIECE_DATA = {
    "rook": {
        "validate": straight_movement,
        "collisions": [straight_collision]
    },
    "bishop": {
        "validate": diagonal_movement,
        "collisions": [diagonal_collision],

        #"forced": {forced_bishop_childpawn: 1}
    },
    "horse": {
        "validate": horse_movement
    },
    "king": {
        "validate": lambda game, origin, destination: abs(origin["y"] - destination["y"]) <= 1 and abs(origin["x"] - destination["x"]) <= 1,
        "collisions": [straight_collision, diagonal_collision]
    },
    "queen": {
        "validate": lambda game, origin, destination: straight_movement(game, origin, destination) or diagonal_movement(game, origin, destination),
        "collisions": [straight_collision, diagonal_collision]
    },
    "antiqueen": {
        "validate": horse_movement,
    },
    "xook": {
        "validate": diagonal_movement,
        "collisions": [diagonal_collision]
    },
    "knook": {
        "validator": straight_movement,
        "validator_capture": horse_movement,
        "collisions_capture": [straight_collision]
    },
    "pawn": {
        "validate": lambda game, origin, destination: pawn_movement(game, origin, destination) or diagonal_movement(game, origin, destination),
        "collisions": [pawn_collision],

        "forced": {enpassant_forced_status: math.inf}
    },
    "child-pawn": {
        "validate": lambda game, origin, destination: pawn_movement(game, origin, destination) or diagonal_movement(game, origin, destination),
        "collisions": [pawn_collision],

        "forced": {enpassant_forced_status: math.inf}
    },
    "archbishop": {
        "validate": lambda game, origin, destination: (abs(origin["x"] - destination["x"]) + abs(origin["y"] - destination["y"])) % 2 == 0,
        "collisions": [straight_collision]
    }
}