import pytest

from app.models.games.game_piece_model import GamePiece
from tests.factories.game import GamePieceFactory
from app.game.board import Board
from app.constants import enums
from app.types import Point
from app.game import pieces

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "piece_type, start_x, start_y, other_pieces, expected_moves",
    # fmt: off
    [
        (
            enums.PieceType.KING, 4, 4, [], {
                Point(4, 5), # up
                Point(5, 3), # up right
                Point(5, 4), # right
                Point(5, 5), # down right
                Point(4, 3), # down
                Point(3, 5), # down left
                Point(3, 4), # left
                Point(3, 3), # up left
            }
        ),
        (
            enums.PieceType.QUEEN, 4, 4, [], {
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
            enums.PieceType.ROOK, 4, 4, [], {
                Point(3, 4), Point(2, 4), Point(1, 4), Point(0, 4), # left
                Point(5, 4), Point(6, 4), Point(7, 4), Point(8, 4), Point(9, 4), # right
                Point(4, 5), Point(4, 6), Point(4, 7), Point(4, 8), Point(4, 9), # up
                Point(4, 3), Point(4, 2), Point(4, 1), Point(4, 0), # down
            }
        ),
        (
            enums.PieceType.HORSIE, 4, 4, [], {
                Point(3, 2), Point(5, 2),
                Point(6, 3), Point(6, 5),
                Point(5, 6), Point(3, 6),
                Point(2, 5), Point(2, 3),
            }
        ),
        (
            enums.PieceType.BISHOP, 4, 4, [], {
                Point(3, 3), Point(2, 2), Point(1, 1), Point(0, 0), # up left
                Point(5, 3), Point(6, 2), Point(7, 1), Point(8, 0), # up right
                Point(3, 5), Point(2, 6), Point(1, 7), Point(0, 8), # down left
                Point(5, 5), Point(6, 6), Point(7, 7), Point(8, 8), Point(9, 9), # down right
            }
        ),
        (
            enums.PieceType.ARCHBISHOP, 4, 4, [], {
                Point(2, 4), Point(0, 4), # left
                Point(6, 4), Point(8, 4), # right
                Point(4, 2), Point(4, 0), # up
                Point(4, 6), Point(4, 8), # down
            }
        ),

        # general edge cases
        (
            enums.PieceType.ROOK, 4, 4, [
                # friendly piece
                GamePieceFactory.build(x=4, y=6),
                # enemy piece
                GamePieceFactory.build(color=enums.Color.BLACK, x=4, y=2),
            ], {
                Point(3, 4), Point(2, 4), Point(1, 4), Point(0, 4), # left
                Point(5, 4), Point(6, 4), Point(7, 4), Point(8, 4), Point(9, 4), # right
                Point(4, 5), # up, blocked by friendly piece
                Point(4, 3), Point(4, 2), # down, captures enemy piece
            }
        ),
        (
            enums.PieceType.ROOK, 9, 9, [], {
                # up
                Point(9, 8), Point(9, 7), Point(9, 6), Point(9, 5),
                Point(9, 4), Point(9, 3), Point(9, 2), Point(9, 1), Point(9, 0),
                # left
                Point(8, 9), Point(7, 9), Point(6, 9), Point(5, 9),
                Point(4, 9), Point(3, 9), Point(2, 9), Point(1, 9), Point(0, 9),
            },
        ),
        (
            enums.PieceType.ROOK, 4, 4, [
                GamePieceFactory.build(x=4, y=5),
                GamePieceFactory.build(x=4, y=3),
                GamePieceFactory.build(x=5, y=4),
                GamePieceFactory.build(x=3, y=4),
            ], set(),
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
    piece_type: enums.PieceType,
    start_x: int,
    start_y: int,
    other_pieces: list[GamePiece],
    expected_moves: set[Point],
):
    """Test if a piece finds the correct legal moves in the given position"""

    piece = GamePieceFactory.build(
        piece_type=piece_type,
        x=start_x,
        y=start_y,
    )
    board = Board([piece] + other_pieces)
    legal_moves = pieces.PIECES[piece_type].calc_legal_moves(
        board, Point(start_x, start_y)
    )
    assert set(legal_moves) == expected_moves
