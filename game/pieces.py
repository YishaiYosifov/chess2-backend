import math

import numpy

from dao import Piece, Square, Game, BOARD_WIDTH, BOARD_HEIGHT

# Forced moves
# @returns
# 0: not forced
# 1: forced, not played
# 2: played
def enpassant_forced_status(game : Game, square : Square, origin : dict, destination : dict) -> list[int, list]:
    if not game.moves: return 0, []

    y_offset = 1 if square.piece.color == "white" else -1
    moves = []
    for x_offset in [-1, 1]:
        if not _can_enpassant(game, square, x_offset): continue

        check_square = game.board[square.y + y_offset, square.x + x_offset]
        moves.append([square.to_dict(), check_square.to_dict()])
        if origin["x"] != square.x or origin["y"] != square.y: continue

        m = (check_square.y - square.y) / (check_square.x - square.x)
        b = square.y - m * square.x
        expected_y = m * destination["x"] + b
        if expected_y == destination["y"]: return 2, []
    return (1, moves) if moves else (0, [])

def bishop_childpawn_forced_status(game : Game, square : Square, origin : dict, destination : dict) -> list[int, list]:
    check_directions = [
        [BOARD_WIDTH, BOARD_HEIGHT],
        [0, BOARD_HEIGHT],
        [0, 0],
        [BOARD_WIDTH, 0]
    ]
    moves = []
    for x, y in check_directions:
        for check_square in diagonal_collision(game, {"x": square.x, "y": square.y}, {"x": x, "y": y}):
            if check_square.piece:
                if check_square.piece.color != square.piece.color and check_square.piece.name == "child-pawn":
                    moves.append([square.to_dict(), check_square.to_dict()])
                    if check_square.x == destination["x"] and \
                        check_square.y == destination["y"] and \
                        origin["x"] == square.x and origin["y"] == square.y: return 2, []
                break
    return (1, moves) if moves else (0, [])

# Collisions
def straight_collision(game : Game, origin : dict, destination : dict) -> numpy.ndarray:
    x1, y1 = origin.values()
    x2, y2 = destination.values()

    if y1 == y2: sliced = game.board[y1, min(x1, x2):max(x1, x2) + 1]
    else: sliced = game.board[min(y1, y2):max(y1, y2) + 1, x1]
    if sliced[-1] == game.board[y1, x1]: sliced = numpy.flip(sliced)
    return sliced[1:]
    
def diagonal_collision(game : Game, origin : dict, destination : dict) -> numpy.ndarray:
    x1, y1 = origin.values()
    x2, y2 = destination.values()

    sliced = game.board[min(y1, y2):max(y1, y2) + 1, min(x1, x2):max(x1, x2) + 1]
    if x1 > x2: sliced = numpy.fliplr(sliced)
    if y1 > y2: sliced = numpy.flipud(sliced)

    diagonal = sliced.diagonal()
    if diagonal[-1] == game.board[y1, x1]: diagonal = numpy.flip(diagonal)
    return diagonal[1:]

def pawn_collision(game : Game, origin : dict, destination : dict) -> bool | numpy.ndarray:
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
    for capture_square in capture_diagonal:
        enpassant_square = game.board[capture_square.y + y_offset][capture_square.x]

        if capture_square.piece or \
            not enpassant_square.piece or \
            not "pawn" in enpassant_square.piece.name or \
            enpassant_square.piece.color == current_piece.color: return False
        enpassant_square.piece = None
    game.board[destination["y"], destination["x"]].piece = current_piece
    return True

def king_collision(game : Game, origin : dict, destination : dict) -> bool | numpy.ndarray:
    king = game.board[origin["y"], origin["x"]]

    x_movement = abs(origin["x"] - destination["x"])
    y_movement = abs(origin["y"] - destination["y"])
    if x_movement == 1 and y_movement == 1: return diagonal_collision(game, origin, destination)
    elif x_movement == 1 or y_movement == 1: return straight_collision(game, origin, destination)
    elif king.piece.moved or y_movement != 0: return False

    if origin["x"] > destination["x"]:
        castle_rook = game.board[origin["y"], 0]
        side = "short"
    else:
        castle_rook = game.board[origin["y"], -1]
        side = "long"
    if castle_rook.piece.moved: return False
    
    between = straight_collision(game, origin, {"x": castle_rook.x, "y": castle_rook.y})[:-1]
    for square in between:
        if square.piece and not (square != between[0] and square.piece.name == "bishop"): return False
    
    if side == "short":
        game.board[origin["y"], 1].piece = king.piece.copy()
        game.board[origin["y"], 2].piece = castle_rook.piece.copy()
    else:
        game.board[origin["y"], 5].piece = king.piece.copy()
        game.board[origin["y"], 4].piece = castle_rook.piece.copy()
    castle_rook.piece = None

    return True

def _can_enpassant(game : Game, square : Square, side : int) -> list:
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

        "forced": {bishop_childpawn_forced_status: 1}
    },
    "horse": {
        "validate": horse_movement
    },
    "king": {
        "validate": lambda game, origin, destination:
            (abs(origin["y"] - destination["y"]) <= 1 and abs(origin["x"] - destination["x"]) <= 1) or \
            (origin["y"] == destination["y"] and abs(origin["x"] - destination["x"]) == 2),
        "collisions": [king_collision]
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