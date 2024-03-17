import pytest

from app.schemas.game_schema import Move
from app.game.board import Board
from app.types import PieceInfo, Point
from app.game import pieces
from app import enums

pytestmark = pytest.mark.unit

# what legal moves do we expect from the piece when placed in the center (4, 4)?
# fmt: off
piece_expected_moves: list[tuple[enums.PieceType, set[Point]]] = [
    (
        enums.PieceType.KING, {
            Point(4, 5), # up
            Point(5, 5), # up right
            Point(5, 4), # right
            Point(5, 3), # down right
            Point(4, 3), # down
            Point(3, 3), # down left
            Point(3, 4), # left
            Point(3, 5), # up left
        }
    ),
    (
        enums.PieceType.QUEEN, {
            Point(4, 5), Point(4, 6), Point(4, 7), Point(4, 8), Point(4, 9), # up
            Point(5, 3), Point(6, 2), Point(7, 1), Point(8, 0), # up right
            Point(5, 4), Point(6, 4), Point(7, 4), Point(8, 4), Point(9, 4), # right
            Point(5, 5), Point(6, 6), Point(7, 7), Point(8, 8), Point(9, 9), # down right
            Point(4, 3), Point(4, 2), Point(4, 1), Point(4, 0), # down
            Point(3, 5), Point(2, 6), Point(1, 7), Point(0, 8), # down left
            Point(3, 4), Point(2, 4), Point(1, 4), Point(0, 4), # left
            Point(3, 3), Point(2, 2), Point(1, 1), Point(0, 0), # up left
        }
    ),
    (
        enums.PieceType.ROOK, {
            Point(3, 4), Point(2, 4), Point(1, 4), Point(0, 4), # left
            Point(5, 4), Point(6, 4), Point(7, 4), Point(8, 4), Point(9, 4), # right
            Point(4, 5), Point(4, 6), Point(4, 7), Point(4, 8), Point(4, 9), # up
            Point(4, 3), Point(4, 2), Point(4, 1), Point(4, 0), # down
        }
    ),
    (
        enums.PieceType.HORSIE, {
            Point(3, 2), Point(5, 2),
            Point(6, 3), Point(6, 5),
            Point(5, 6), Point(3, 6),
            Point(2, 5), Point(2, 3),
        }
    ),
    (
        enums.PieceType.BISHOP, {
            Point(3, 3), Point(2, 2), Point(1, 1), Point(0, 0), # up left
            Point(5, 3), Point(6, 2), Point(7, 1), Point(8, 0), # up right
            Point(3, 5), Point(2, 6), Point(1, 7), Point(0, 8), # down left
            Point(5, 5), Point(6, 6), Point(7, 7), Point(8, 8), Point(9, 9), # down right
        }
    ),
    (
        enums.PieceType.ARCHBISHOP, {
            Point(2, 4), Point(0, 4), # left
            Point(6, 4), Point(8, 4), # right
            Point(4, 2), Point(4, 0), # up
            Point(4, 6), Point(4, 8), # down
        }
    )
]
# fmt: on

piece_edge_cases_ids = [
    "general edge case: in the center, blocked by friendly and enemy pieces",
    "general edge case: in the corner (plotting world domination)",
    "general edge case: blocked by friendly pieces, no legal moves",
]
# fmt: off
piece_edge_cases: list[tuple[enums.PieceType, Point, str, dict[Point, Move]]] = [
    # general edge cases
    (
        enums.PieceType.ROOK, Point(4, 4),
        "10/10/10/4P5/10/4R5/10/4p5/10/10", {
            # left
            Point(3, 4): Move(),
            Point(2, 4): Move(),
            Point(1, 4): Move(),
            Point(0, 4): Move(),
            Point(5, 4): Move(),
            Point(6, 4): Move(),
            Point(7, 4): Move(),
            Point(8, 4): Move(),

            # right
            Point(9, 4): Move(),

            # up, blocked by friendly piece
            Point(4, 5): Move(),

            # down, captures enemy piece
            Point(4, 3): Move(),
            Point(4, 2): Move(captured=[Point(4, 2)]),
        },
    ),
    (
        enums.PieceType.ROOK, Point(9, 9),
        "10/10/10/10/10/10/10/10/10/10", {
            # up
            Point(9, 8): Move(),
            Point(9, 7): Move(),
            Point(9, 6): Move(),
            Point(9, 5): Move(),
            Point(9, 4): Move(),
            Point(9, 3): Move(),
            Point(9, 2): Move(),
            Point(9, 1): Move(),
            Point(9, 0): Move(),

            # left
            Point(8, 9): Move(),
            Point(7, 9): Move(),
            Point(6, 9): Move(),
            Point(5, 9): Move(),
            Point(4, 9): Move(),
            Point(3, 9): Move(),
            Point(2, 9): Move(),
            Point(1, 9): Move(),
            Point(0, 9): Move(),
        },
    ),
    (
        enums.PieceType.ROOK, Point(4, 4),
        "10/10/10/10/4P5/3PRP4/4P5/10/10/10", {}
    )
]
# fmt: on


@pytest.mark.parametrize(
    "piece_type, expected_moves",
    piece_expected_moves,
    ids=[f"{case[0].name.lower()} moves" for case in piece_expected_moves],
)
def test_piece_moves(piece_type: enums.PieceType, expected_moves: set[Point]):
    """
    Test that the piece can find the correct moves
    when nothing is blocking it and it's right in the center
    """

    piece_position = Point(4, 4)

    board = Board()
    board[piece_position] = PieceInfo(piece_type, enums.Color.WHITE)

    legal_moves = pieces.PIECES[piece_type].calc_legal_moves(
        board, piece_position
    )
    assert set(legal_moves) == expected_moves

    regular_move = Move()
    for move in legal_moves.values():
        assert move == regular_move


@pytest.mark.parametrize(
    "piece_type, piece_position, fen, expected_moves",
    piece_edge_cases,
    ids=piece_edge_cases_ids,
)
def test_piece_edge_cases(
    piece_type: enums.PieceType,
    piece_position: Point,
    fen: str,
    expected_moves: dict[Point, Move],
):
    """Set up the board in a specific position to check edge cases"""

    board = Board.from_fen(fen)

    legal_moves = pieces.PIECES[piece_type].calc_legal_moves(
        board, piece_position
    )
    assert legal_moves == expected_moves
