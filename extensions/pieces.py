from __future__ import annotations
from typing import TYPE_CHECKING

import math

import numpy

from .board import Square, Piece, BOARD_HEIGHT, BOARD_WIDTH
if TYPE_CHECKING: from dao import Game

# region Forced moves

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

# endregion

# region Collisions

def straight_collision(game : Game, origin : dict, destination : dict, include_first = False) -> numpy.ndarray:
    x1, y1 = origin.values()
    x2, y2 = destination.values()

    if y1 == y2: sliced = game.board[y1, min(x1, x2):max(x1, x2) + 1]
    else: sliced = game.board[min(y1, y2):max(y1, y2) + 1, x1]
    
    if sliced[-1] == game.board[y1, x1]: sliced = numpy.flip(sliced)
    if not include_first: sliced = sliced[1:]
    return sliced
    
def diagonal_collision(game : Game, origin : dict, destination : dict, include_first = False) -> numpy.ndarray:
    x1, y1 = origin.values()
    x2, y2 = destination.values()

    sliced = game.board[min(y1, y2):max(y1, y2) + 1, min(x1, x2):max(x1, x2) + 1]
    if x1 > x2: sliced = numpy.fliplr(sliced)
    if y1 > y2: sliced = numpy.flipud(sliced)

    diagonal = sliced.diagonal()
    if diagonal[-1] == game.board[y1, x1]: diagonal = numpy.flip(diagonal)
    if not include_first: diagonal = diagonal[1:]
    return diagonal

def pawn_collision(game : Game, origin : dict, destination : dict) -> dict | numpy.ndarray:
    if not diagonal_movement(game, origin, destination): return straight_collision(game, origin, destination)

    if not game.moves: return numpy.empty()
    pawn_square : Piece = game.board[origin["y"]][origin["x"]]
    pawn_piece = pawn_square.piece

    # regular capture
    x_offset = 1 if destination["x"] > origin["x"] else -1
    y_offset = 1 if pawn_square.piece.color == "white" else -1

    regular_capture_square = game.board[pawn_square.y + y_offset, pawn_square.x + x_offset]
    if regular_capture_square.piece:
        if abs(origin["y"] - destination["y"]) > 1 or pawn_piece.color == regular_capture_square.piece.color: return {"success": False}
        return numpy.asarray([regular_capture_square])

    # en passant
    if not _can_enpassant(game, pawn_square, x_offset): return {"success": False}

    _, captured = _get_enpassant_diagonal(game, pawn_square, destination["x"], destination["y"], True)
    game.board[destination["y"], destination["x"]].piece = pawn_piece
    return {"success": True, "move_log_portion": {"moved": [{"piece": pawn_piece.name, "origin": origin, "destination": destination}], "captured": list(captured)}}

def king_collision(game : Game, origin : dict, destination : dict) -> dict:
    king = game.board[origin["y"], origin["x"]]

    x_movement = abs(origin["x"] - destination["x"])
    y_movement = abs(origin["y"] - destination["y"])
    if x_movement == 1 and y_movement == 1: return diagonal_collision(game, origin, destination)
    elif x_movement == 1 or y_movement == 1: return straight_collision(game, origin, destination)

    # Castling
    if x_movement == 0 and y_movement > 0:
        # Vertical Castle
        if king.y == 0:
            castle_rook = game.board[-1, origin["x"]]
            new_rook_position = {"x": origin["x"], "y": math.floor(BOARD_HEIGHT / 2) - 1}
        elif king.y == BOARD_HEIGHT - 1:
            castle_rook = game.board[0, origin["x"]]
            new_rook_position = {"x": origin["x"], "y": math.floor(BOARD_HEIGHT / 2)}
        else: return {"success": False}
    else:
        # Regular Castle
        if king.piece.moved or y_movement != 0: return {"success": False}

        if origin["x"] > destination["x"]:
            castle_rook = game.board[origin["y"], 0]
            new_rook_position = {"x": 3, "y": origin["y"]}
        else:
            castle_rook = game.board[origin["y"], -1]
            new_rook_position = {"x": 5, "y": origin["y"]}
        if castle_rook.piece and castle_rook.piece.moved: {"success": False}

    if not castle_rook.piece: {"success": False}

    between = straight_collision(game, origin, {"x": castle_rook.x, "y": castle_rook.y})[:-1]
    captured = []
    for square in between:
        if square.piece:
            if square != between[0] or square.piece.name != "bishop": {"success": False}
            captured.append({"piece": square.piece.name, "x": square.x, "y": square.y})

    game.board[destination["y"], destination["x"]].piece = king.piece.copy()
    game.board[new_rook_position["y"], new_rook_position["x"]].piece = castle_rook.piece.copy()
    castle_rook.piece = None

    return {"success": True, "move_log_portion": {
                "moved": [
                    {"piece": "king", "origin": origin, "destination": destination},
                    {"piece": "rook", "origin": {"x": castle_rook.x, "y": castle_rook.y}, "destination": new_rook_position}
                ], "captured": captured}}

def bishop_collision(game : Game, origin : dict, destination : dict) -> bool | numpy.ndarray:
    bishop = game.board[origin["y"], origin["x"]]
    if diagonal_movement(game, origin, destination):
        if game.board[destination["y"], destination["x"]].piece and \
            game.board[destination["y"], destination["x"]].piece.color == bishop.piece.color: return {"success": False}
        return diagonal_collision(game, origin, destination)

    if origin["x"] == destination["x"]:
        y_offset = 1 if origin["y"] > destination["y"] else -1
        new_ilvaticano_position = {"x": destination["x"], "y": destination["y"] + y_offset}
        try: ilvaticano_bud = game.board[destination["y"] - y_offset, destination["x"]]
        except IndexError: return {"success": False}
    else:
        x_offset = 1 if origin["x"] > destination["x"] else -1
        new_ilvaticano_position = {"x": destination["x"] + x_offset, "y": destination["y"]}
        try: ilvaticano_bud = game.board[destination["y"], destination["x"] - x_offset]
        except IndexError: return {"success": False}
    ilvaticano_moves = _get_ilvaticano_moves(game, origin, ilvaticano_bud)
    if not ilvaticano_moves: return {"success": False}
    
    captured = []
    for square in ilvaticano_moves:
        captured.append({"piece": square.piece.name, "x": square.x, "y": square.y})
        square.piece = None

    move_log = {
        "moved": [
            {"piece": bishop.piece.name, "origin": origin, "destination": destination},
            {"piece": ilvaticano_bud.piece.name, "origin": {"x": ilvaticano_bud.x, "y": ilvaticano_bud.y}, "destination": new_ilvaticano_position}
        ], "captured": captured
    }

    game.board[destination["y"], destination["x"]].piece = bishop.piece.copy()
    game.board[new_ilvaticano_position["y"], new_ilvaticano_position["x"]].piece = ilvaticano_bud.piece.copy()
    ilvaticano_bud.piece = None

    return {"success": True, "move_log_portion": move_log}

# endregion

# region All Legal

def piece_slice(pieces : numpy.ndarray, allow_capture = True) -> numpy.ndarray:
    fromPiece = pieces[0].piece

    pieces = numpy.delete(pieces, 0)
    for index, square in enumerate(pieces):
        if square.piece: return pieces[:index + (1 if fromPiece.color != square.piece.color and allow_capture else 0)]
    return pieces

straight_legal = lambda game, origin: numpy.concatenate(
                                        (
                                            piece_slice(straight_collision(game, origin, {"x": 0, "y": origin["y"]}, True)),
                                            piece_slice(straight_collision(game, origin, {"x": BOARD_WIDTH, "y": origin["y"]}, True)),
                                            piece_slice(straight_collision(game, origin, {"x": origin["x"], "y": BOARD_HEIGHT}, True)),
                                            piece_slice(straight_collision(game, origin, {"x": origin["x"], "y": 0}, True))
                                        ))
diagonal_legal = lambda game, origin: numpy.concatenate(
                                        (
                                            piece_slice(diagonal_collision(game, origin, {"x": BOARD_WIDTH, "y": BOARD_HEIGHT}, True)),
                                            piece_slice(diagonal_collision(game, origin, {"x": 0, "y": BOARD_HEIGHT}, True)),
                                            piece_slice(diagonal_collision(game, origin, {"x": 0, "y": 0}, True)),
                                            piece_slice(diagonal_collision(game, origin, {"x": BOARD_WIDTH, "y": 0}, True))
                                        ))

def king_legal(game : Game, origin : dict) -> numpy.ndarray:
    king : Square = game.board[origin["y"], origin["x"]]

    moves = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0: continue

            check_x = origin["x"] - i
            check_y = origin["y"] - j
            if (check_x < 0 or check_x > BOARD_WIDTH - 1 or check_y < 0 or check_y > BOARD_HEIGHT - 1): continue

            square = game.board[check_y][check_x]
            if square.piece and square.piece.color == king.piece.color: continue
            moves.append(square)

    # Vertical Castle
    if king.y == 0: moves += _get_castle_moves(game, origin, game.board[BOARD_HEIGHT - 1, origin["x"]], is_vertical=True) or []
    elif king.y == BOARD_HEIGHT - 1: moves += _get_castle_moves(game, origin, game.board[0, origin["x"]], is_vertical=True) or []

    # Regular Castle
    if not king.piece.moved:
        for castle_direction in [0, BOARD_WIDTH - 1]: moves += _get_castle_moves(game, origin, game.board[origin["y"], castle_direction]) or []

    return moves

def horse_legal(game : Game, origin : dict) -> numpy.ndarray:
    horse = game.board[origin["y"], origin["x"]].piece

    moves = []
    for i in [-2, -1, 1, 2]:
        for j in [-2, -1, 1, 2]:
            if abs(i) == abs(j): continue

            check_x = origin["x"] - i
            check_y = origin["y"] - j
            if check_x < 0 or check_x > BOARD_WIDTH - 1 or check_y < 0 or check_y > BOARD_HEIGHT - 1: continue

            check_square = game.board[check_y][check_x]
            if check_square.piece and check_square.piece.color == horse.color: continue
            moves.append(check_square)
    return moves

def pawn_legal(game : Game, origin : dict) -> numpy.ndarray:
    pawn : Square = game.board[origin["y"], origin["x"]]

    limit = _get_pawn_limit(pawn)
    if pawn.piece.color == "white":
        moves = list(piece_slice(game.board[origin["y"]:origin["y"] + limit + 1, origin["x"]], False))
        y_slice = BOARD_HEIGHT
    else:
        moves = list(piece_slice(game.board[origin["y"] - limit:origin["y"] + 1, origin["x"]][::-1], False))
        y_slice = 0
    if not game.moves: return moves

    y_offset = 1 if pawn.piece.color == "white" else -1
    for x_slice in [0, BOARD_WIDTH]:
        side = 1 if x_slice > origin["x"] else -1

        try: check_capture_square = game.board[origin["y"] + y_offset, origin["x"] + side]
        except IndexError: continue
        if check_capture_square.piece and check_capture_square.piece.color != pawn.piece.color:
            moves.append(check_capture_square)
            continue
        elif not _can_enpassant(game, pawn, side): continue

        enpassant_slice, _ = _get_enpassant_diagonal(game, pawn, x_slice, y_slice)
        moves += list(enpassant_slice)
    return moves

def bishop_legal(game : Game, origin : dict) -> numpy.ndarray:
    moves = list(diagonal_legal(game, origin))
    
    # Il Vaticano
    for i in [-3, 0, 3]:
        for j in [-3, 0, 3]:
            if i == j == 0: continue

            check_x = origin["x"] + j
            check_y = origin["y"] + i
            if check_x > BOARD_WIDTH - 1 or check_x < 0 or check_y > BOARD_HEIGHT - 1 or check_y < 0: continue

            ilvaticano_bud = game.board[check_y, check_x]
            ilvaticano_moves = _get_ilvaticano_moves(game, origin, ilvaticano_bud)
            if ilvaticano_moves: moves += ilvaticano_moves + [ilvaticano_bud]
    return moves

# endregion
        
# region Piece movement

straight_movement = lambda game, origin, destination: origin["x"] == destination["x"] or origin["y"] == destination["y"]
diagonal_movement = lambda game, origin, destination: abs(origin["x"] - destination["x"]) == abs(origin["y"] - destination["y"])
horse_movement = lambda game, origin, destination: (abs(origin["y"] - destination["y"]) == 2 and abs(origin["x"] - destination["x"]) == 1) or \
                                                (abs(origin["y"] - destination["y"]) == 1 and abs(origin["x"] - destination["x"]) == 2)

def pawn_movement(game : Game, origin : dict, destination : dict) -> bool:
    pawn : Piece = game.board[origin["y"], origin["x"]]
    return origin["x"] == destination["x"] and abs(destination["y"] - origin["y"]) <= _get_pawn_limit(pawn)

bishop_movement = lambda game, origin, destination: diagonal_movement(game, origin, destination) or (
                                                        straight_movement(game, origin, destination) and (
                                                            abs(origin["y"] - destination["y"]) == 2 or \
                                                            abs(origin["x"] - destination["x"]) == 2
                                                        )
                                                    )

# endregion

# region Helpers

def _can_enpassant(game : Game, square : Square, side : int) -> list:
    if not game.moves: return False

    last_move = game.moves[-1]
    for move in last_move["moved"]:
        if not "pawn" in move["piece"] or \
            move["destination"] != {"x": square.x + side, "y": square.y} or \
            abs(move["destination"]["y"] - move["origin"]["y"]) < 2 or \
            move["origin"]["x"] != move["destination"]["x"]: continue
        return True
    return False

def _get_pawn_limit(pawnSquare : Square) -> int:
    if not pawnSquare.piece.moved:
        half_board_width = BOARD_WIDTH / 2
        if (BOARD_WIDTH % 2 == 0 and \
                (pawnSquare.x == half_board_width - 1 or \
                pawnSquare.x == half_board_width)) or \
            (BOARD_WIDTH % 2 != 0 and pawnSquare.x == math.floor(half_board_width)): return 3
        else: return 2
    else: return 1

def _get_enpassant_diagonal(game : Game, pawn_square : Square, x_slice : int, y_slice : int, capture = False) -> tuple[numpy.ndarray, list]:
    enpassant_slice = diagonal_collision(game, {"x": pawn_square.x, "y": pawn_square.y}, {"x": x_slice, "y": y_slice})
    y_offset = -1 if pawn_square.piece.color == "white" else 1

    captured = []
    for index, enpassant_square in enumerate(enpassant_slice):
        capture_square = game.board[enpassant_square.y + y_offset, enpassant_square.x]
        if capture_square.piece and \
            not enpassant_square.piece and \
            "pawn" in capture_square.piece.name and \
            capture_square.piece.color != pawn_square.piece.color:
            captured.append({"piece": capture_square.piece.name, "x": capture_square.x, "y": capture_square.y})
            if capture: capture_square.piece = None
        else:
            enpassant_slice = enpassant_slice[:index]
            break
    return enpassant_slice, captured

def _get_castle_moves(game : Game, origin : dict, castle_rook : Square, is_vertical = False) -> list | None:
    if not castle_rook.piece or \
        castle_rook.piece.color != game.board[origin["y"], origin["x"]].piece.color or \
        castle_rook.piece.name != "rook" or \
        (not is_vertical and castle_rook.piece.moved): return

    between = straight_collision(game, origin, {"x": castle_rook.x, "y": castle_rook.y})
    
    castle_moves = []
    for square in between:
        if square.piece:
            if not is_vertical and square == between[0] and square.piece.name == "bishop": continue
            elif not (square == between[-1] and square.piece.name == "rook"): break
        castle_moves.append(square)
    else: return castle_moves

def _get_ilvaticano_moves(game : Game, origin : dict, ilvaticano_bud : Square) -> list:
    bishop : Piece = game.board[origin["y"], origin["x"]].piece
    if not ilvaticano_bud.piece or \
        (ilvaticano_bud.piece.name != "bishop" and ilvaticano_bud.piece.name != "xook") or \
        ilvaticano_bud.piece.color != bishop.color: return

    ilvaticano_capture = straight_collision(game, origin, {"x": ilvaticano_bud.x, "y": ilvaticano_bud.y})[:-1]
    for ilvaticano_square in ilvaticano_capture:
        if not ilvaticano_square.piece or not "pawn" in ilvaticano_square.piece.name or ilvaticano_square.piece.color == bishop.color: break
    else: return list(ilvaticano_capture)

# endregion

PIECE_DATA = {
    "rook": {
        "validate": straight_movement,
        "collisions": [straight_collision],

        "all_legal": straight_legal
    },
    "bishop": {
        "validate": bishop_movement,
        "collisions": [bishop_collision],

        "forced": {bishop_childpawn_forced_status: 1},
        "all_legal": bishop_legal,
        "allow_same_color_capture": True
    },
    "horse": {
        "validate": horse_movement,
        "all_legal": horse_legal
    },
    "king": {
        "validate": lambda game, origin, destination:
            (abs(origin["y"] - destination["y"]) <= 1 and abs(origin["x"] - destination["x"]) <= 1) or \
            (origin["y"] == destination["y"] and abs(origin["x"] - destination["x"]) == 2) or \
            (origin["x"] == destination["x"] and abs(origin["y"] - destination["y"]) == math.floor(BOARD_WIDTH / 2) + 1),
        "collisions": [king_collision],

        "all_legal": king_legal,
        "allow_same_color_capture": True
    },
    "queen": {
        "validate": lambda game, origin, destination: straight_movement(game, origin, destination) or diagonal_movement(game, origin, destination),
        "collisions": [straight_collision, diagonal_collision],

        "all_legal": lambda game, origin: numpy.concatenate((straight_legal(game, origin), diagonal_legal(game, origin)))
    },
    "antiqueen": {
        "validate": horse_movement,
        "all_legal": horse_legal
    },
    "xook": {
        "validate": bishop_movement,
        "collisions": [bishop_collision],

        "all_legal": bishop_legal,
        "allow_same_color_capture": True
    },
    "knook": {
        "validator": straight_movement,
        "validator_capture": horse_movement,
        "collisions_capture": [straight_collision],

        "all_legal": lambda game, origin: [square for square in straight_legal(game, origin) if square.piece] + \
                                            [square for square in horse_legal(game, origin) if not square.piece]
    },
    "pawn": {
        "validate": lambda game, origin, destination: pawn_movement(game, origin, destination) or diagonal_movement(game, origin, destination),
        "collisions": [pawn_collision],

        "forced": {enpassant_forced_status: math.inf},
        "all_legal": pawn_legal
    },
    "child-pawn": {
        "validate": lambda game, origin, destination: pawn_movement(game, origin, destination) or diagonal_movement(game, origin, destination),
        "collisions": [pawn_collision],

        "forced": {enpassant_forced_status: math.inf},
        "all_legal": pawn_legal
    },
    "archbishop": {
        "validate": lambda game, origin, destination: (abs(origin["x"] - destination["x"]) + abs(origin["y"] - destination["y"])) % 2 == 0,
        "collisions": [straight_collision],

        "all_legal": lambda game, origin: [
                                                square for square in straight_legal(game, origin)
                                                if (square.x + square.y) % 2 == (
                                                    1 if game.board[origin["y"], origin["x"]].piece.color == "white" else 0
                                                )
                                            ]
    }
}