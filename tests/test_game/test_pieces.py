import pytest

from tests.factories.game import GamePieceFactory
from app.game.board import Board
from app.constants import enums
from app.types import Point
from app.game import pieces


@pytest.mark.unit
class TestRook:
    def test_moves(self):
        board = Board(
            [GamePieceFactory.build(piece_type=enums.Piece.ROOK, x=4, y=4)]
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
            Point(4, 5), Point(4, 6), Point(4, 7), Point(4, 8), Point(4, 9), # move up
            Point(4, 3), Point(4, 2), Point(4, 1), Point(4, 0), # move down
        }
        # fmt: on

        assert legal_moves == expected_moves

    def test_friendly_piece_blocks_path(self):
        board = Board(
            [
                GamePieceFactory.build(piece_type=enums.Piece.ROOK, x=4, y=4),
                GamePieceFactory.build(x=4, y=6),
            ]
        )

        legal_moves = set(pieces.Rook.calc_legal_moves(board, Point(4, 4)))

        # fmt: off
        expected_moves = {
            Point(3, 4), Point(2, 4), Point(1, 4), Point(0, 4), # move left
            Point(5, 4), Point(6, 4), Point(7, 4), Point(8, 4), Point(9, 4), # move right
            Point(4, 5), # move up
            Point(4, 3), Point(4, 2), Point(4, 1), Point(4, 0), # move down
        }
        # fmt: on

        assert legal_moves == expected_moves

    def test_captures_enemy_piece(self):
        board = Board(
            [
                GamePieceFactory.build(piece_type=enums.Piece.ROOK, x=4, y=4),
                GamePieceFactory.build(color=enums.Color.BLACK, x=4, y=6),
            ]
        )

        legal_moves = set(pieces.Rook.calc_legal_moves(board, Point(4, 4)))

        # fmt: off
        expected_moves = {
            Point(3, 4), Point(2, 4), Point(1, 4), Point(0, 4), # move left
            Point(5, 4), Point(6, 4), Point(7, 4), Point(8, 4), Point(9, 4), # move right
            Point(4, 5), Point(4, 6), # move up
            Point(4, 3), Point(4, 2), Point(4, 1), Point(4, 0), # move down
        }
        # fmt: on

        assert legal_moves == expected_moves
