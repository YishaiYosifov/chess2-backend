import pytest

from app.game.board import Board
from app.types import PieceInfo, Point
from app import enums

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "fen, expected_board",
    [
        ("10/10/10/10/10/10/10/10/10/10", {}),
        (
            "Q9/10/10/10/10/10/10/10/10/10",
            {Point(0, 9): PieceInfo(enums.PieceType.QUEEN, enums.Color.WHITE)},
        ),
        (
            "rh7r/10/c8c/10/10/4B5/10/10/RrRRRRRRRR/10",
            {
                Point(0, 9): PieceInfo(enums.PieceType.ROOK, enums.Color.BLACK),
                Point(1, 9): PieceInfo(
                    enums.PieceType.HORSIE,
                    enums.Color.BLACK,
                ),
                Point(9, 9): PieceInfo(enums.PieceType.ROOK, enums.Color.BLACK),
                Point(0, 7): PieceInfo(
                    enums.PieceType.ARCHBISHOP,
                    enums.Color.BLACK,
                ),
                Point(9, 7): PieceInfo(
                    enums.PieceType.ARCHBISHOP,
                    enums.Color.BLACK,
                ),
                Point(4, 4): PieceInfo(
                    enums.PieceType.BISHOP,
                    enums.Color.WHITE,
                ),
                Point(0, 1): PieceInfo(enums.PieceType.ROOK, enums.Color.WHITE),
                Point(1, 1): PieceInfo(enums.PieceType.ROOK, enums.Color.BLACK),
                Point(2, 1): PieceInfo(enums.PieceType.ROOK, enums.Color.WHITE),
                Point(3, 1): PieceInfo(enums.PieceType.ROOK, enums.Color.WHITE),
                Point(4, 1): PieceInfo(enums.PieceType.ROOK, enums.Color.WHITE),
                Point(5, 1): PieceInfo(enums.PieceType.ROOK, enums.Color.WHITE),
                Point(6, 1): PieceInfo(enums.PieceType.ROOK, enums.Color.WHITE),
                Point(7, 1): PieceInfo(enums.PieceType.ROOK, enums.Color.WHITE),
                Point(8, 1): PieceInfo(enums.PieceType.ROOK, enums.Color.WHITE),
                Point(9, 1): PieceInfo(enums.PieceType.ROOK, enums.Color.WHITE),
            },
        ),
    ],
)
def test_initializes_from_fen(fen: str, expected_board: dict[Point, PieceInfo]):
    """Test that the board is created correctly"""

    board = Board.from_fen(fen, 10, 10)
    assert board._board == expected_board


@pytest.mark.parametrize(
    "fen",
    [
        "Q10/10/10/10/10/10/10/10/10/10",
        "1/10/10/10/10/10/10/10/10/10",
        "10/10/10/10/10/10/10/10/10/10/10",
        "10/10/10/10/10/10/10/10/10",
    ],
    ids=[
        "too many squares in last rank",
        "too little squares in last rank",
        "too many ranks",
        "too little ranks",
    ],
)
def test_raises_error_when_initializing_out_of_bound(
    fen: str,
):
    """Test that ValueError is raised when a piece is attempted to be placed out of the board"""

    board_width = 10
    board_height = 10

    with pytest.raises(ValueError):
        Board.from_fen(fen, board_width, board_height)


def test_initializes_empty_without_fen():
    assert Board()._board == {}
