import pytest

from app.models.games.game_piece_model import GamePiece
from tests.factories.game import GamePieceFactory
from app.game.board import Board
from app.constants import enums
from app.types import Point


@pytest.mark.unit
@pytest.mark.parametrize(
    "pieces",
    [
        [
            GamePieceFactory.build(piece_type=enums.PieceType.PAWN, x=0, y=0),
            GamePieceFactory.build(piece_type=enums.PieceType.ROOK, x=0, y=9),
        ],
        [],
    ],
)
def test_initializes_from_pieces(pieces: list[GamePiece]):
    """Test that the board is created correctly"""

    board = Board(pieces)

    assert len(board._board) == len(pieces)
    for piece in pieces:
        position = Point(piece.x, piece.y)
        indexed_piece = board._board.get(position)
        assert indexed_piece == piece


@pytest.mark.unit
@pytest.mark.parametrize(
    "pieces",
    [
        [GamePieceFactory.build(piece_type=enums.PieceType.PAWN, x=-1, y=0)],
        [GamePieceFactory.build(piece_type=enums.PieceType.PAWN, x=10, y=0)],
        [GamePieceFactory.build(piece_type=enums.PieceType.PAWN, x=0, y=-1)],
        [GamePieceFactory.build(piece_type=enums.PieceType.PAWN, x=0, y=10)],
    ],
)
def test_raises_error_when_initializing_out_of_bound(
    pieces: list[GamePiece],
):
    """Test that ValueError is raised when a piece is attempted to be placed out of the board"""
    board_width = 10
    board_height = 10

    with pytest.raises(ValueError):
        Board(pieces, board_width, board_height)
