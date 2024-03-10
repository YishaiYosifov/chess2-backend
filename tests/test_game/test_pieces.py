import pytest

from tests.factories.game import PieceInfoFactory
from app.game.board import Board
from app.types import PieceInfo, Point
from app.game import pieces
from app import enums

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "piece_type, piece_position, other_pieces, expected_moves",
    # fmt: off
    [
        (
            enums.PieceType.KING, Point(4, 4), {}, {
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
            enums.PieceType.QUEEN, Point(4, 4), {}, {
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
            enums.PieceType.ROOK, Point(4, 4), {}, {
                Point(3, 4), Point(2, 4), Point(1, 4), Point(0, 4), # left
                Point(5, 4), Point(6, 4), Point(7, 4), Point(8, 4), Point(9, 4), # right
                Point(4, 5), Point(4, 6), Point(4, 7), Point(4, 8), Point(4, 9), # up
                Point(4, 3), Point(4, 2), Point(4, 1), Point(4, 0), # down
            }
        ),
        (
            enums.PieceType.HORSIE, Point(4, 4), {}, {
                Point(3, 2), Point(5, 2),
                Point(6, 3), Point(6, 5),
                Point(5, 6), Point(3, 6),
                Point(2, 5), Point(2, 3),
            }
        ),
        (
            enums.PieceType.BISHOP, Point(4, 4), {}, {
                Point(3, 3), Point(2, 2), Point(1, 1), Point(0, 0), # up left
                Point(5, 3), Point(6, 2), Point(7, 1), Point(8, 0), # up right
                Point(3, 5), Point(2, 6), Point(1, 7), Point(0, 8), # down left
                Point(5, 5), Point(6, 6), Point(7, 7), Point(8, 8), Point(9, 9), # down right
            }
        ),
        (
            enums.PieceType.ARCHBISHOP, Point(4, 4), {}, {
                Point(2, 4), Point(0, 4), # left
                Point(6, 4), Point(8, 4), # right
                Point(4, 2), Point(4, 0), # up
                Point(4, 6), Point(4, 8), # down
            }
        ),

        # general edge cases
        (
            enums.PieceType.ROOK, Point(4, 4), {
                Point(4,6): PieceInfoFactory(),
                Point(4, 2): PieceInfoFactory(color=enums.Color.BLACK)
            }, {
                Point(3, 4), Point(2, 4), Point(1, 4), Point(0, 4), # left
                Point(5, 4), Point(6, 4), Point(7, 4), Point(8, 4), Point(9, 4), # right
                Point(4, 5), # up, blocked by friendly piece
                Point(4, 3), Point(4, 2), # down, captures enemy piece
            }
        ),
        (
            enums.PieceType.ROOK, Point(9, 9), {}, {
                # up
                Point(9, 8), Point(9, 7), Point(9, 6), Point(9, 5),
                Point(9, 4), Point(9, 3), Point(9, 2), Point(9, 1), Point(9, 0),
                # left
                Point(8, 9), Point(7, 9), Point(6, 9), Point(5, 9),
                Point(4, 9), Point(3, 9), Point(2, 9), Point(1, 9), Point(0, 9),
            },
        ),
        (
            enums.PieceType.ROOK, Point(4, 4), {
                Point(4, 5): PieceInfoFactory(),
                Point(4, 3): PieceInfoFactory(),
                Point(5, 4): PieceInfoFactory(),
                Point(3, 4): PieceInfoFactory(),
            }, set(),
        ),
    ],
    # fmt: on
    ids=[
        "king moves",
        "queen moves",
        "rook moves",
        "horsie moves",
        "bishop moves",
        "archbishop moves",
        "general edge case: in the center, blocked by friendly and enemy pieces",
        "general edge case: in the corner (plotting world domination)",
        "general edge case: blocked by friendly pieces, no legal moves",
    ],
)
def test_piece_moves(
    piece_position: Point,
    piece_type: enums.PieceType,
    other_pieces: dict[Point, PieceInfo],
    expected_moves: set[Point],
):
    """Test if a piece finds the correct legal moves in the given position"""

    board = Board()
    board[piece_position] = PieceInfo(piece_type, enums.Color.WHITE)

    for other_piece_position, other_piece in other_pieces.items():
        board[other_piece_position] = other_piece

    legal_moves = pieces.PIECES[piece_type].calc_legal_moves(
        board, piece_position
    )
    assert set(legal_moves) == expected_moves
