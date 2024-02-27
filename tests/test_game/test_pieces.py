from tests.factories.game import GamePieceFactory
from app.game.board import Board
from app.constants import enums
from app.types import Point
from app.game import pieces


def test_rook_moves():
    board = Board(
        [
            GamePieceFactory.build(
                piece_type=enums.PieceType.ROOK,
                x=4,
                y=4,
            ),
            # friendly piece
            GamePieceFactory.build(x=4, y=6),
            # enemy piece
            GamePieceFactory.build(color=enums.Color.BLACK, x=4, y=2),
        ]
    )

    legal_moves = set(
        pieces.Rook.calc_legal_moves(
            board,
            Point(4, 4),
        )
    )

    # fmt: off
    expected_moves = {
        Point(3, 4), Point(2, 4), Point(1, 4), Point(0, 4), # move left
        Point(5, 4), Point(6, 4), Point(7, 4), Point(8, 4), Point(9, 4), # move right
        Point(4, 5), # move up, blocked by friendly piece
        Point(4, 3), Point(4, 2), # move down, captures enemy piece
    }
    # fmt: on

    assert legal_moves == expected_moves
