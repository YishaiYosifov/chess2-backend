from tests.factories.game import GamePieceFactory
from app.constants import enums
from app.pieces import pieces
from app.types import Point, Board


def place_piece(
    x: int,
    y: int,
    piece: enums.Piece,
    color: enums.Color = enums.Color.WHITE,
    board: Board | None = None,
):
    if not board:
        board = {}

    board[Point(x, y)] = GamePieceFactory.build(
        piece=piece,
        color=color,
        x=x,
        y=y,
    )
    return board


class TestRook:
    rook_position = Point(4, 4)
    board = place_piece(rook_position.x, rook_position.y, enums.Piece.ROOK)

    def test_moves(self):
        legal_moves = set(
            pieces.Rook.calc_legal_moves(
                self.board,
                self.rook_position,
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
        place_piece(4, 6, enums.Piece.ROOK, board=self.board)
        legal_moves = set(pieces.Rook.calc_legal_moves(self.board, Point(4, 4)))

        # fmt: off
        expected_moves = {
            Point(3, 4), Point(2, 4), Point(1, 4), Point(0, 4), # move left
            Point(5, 4), Point(6, 4), Point(7, 4), Point(8, 4), Point(9, 4), # move right
            Point(4, 5), # move up
            Point(4, 3), Point(4, 2), Point(4, 1), Point(4, 0), # move down
        }
        # fmt: on

        assert legal_moves == expected_moves
