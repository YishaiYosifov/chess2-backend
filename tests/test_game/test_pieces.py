import pytest

from app.models.games.game_piece_model import GamePiece
from tests.factories.game import GamePieceFactory
from app.game.board import Board
from app.constants import enums
from app.types import Point
from app.game import pieces

pytestmark = pytest.mark.unit


def get_horizontal_moves(from_x: int, from_y: int, to_x: int) -> set[Point]:
    return {Point(i, from_y) for i in range(from_x, to_x + 1)}


def get_vertical_moves(from_x: int, from_y: int, to_y: int) -> set[Point]:
    return {Point(from_x, i) for i in range(from_y, to_y + 1)}


def assert_moves(
    piece_type: enums.PieceType,
    start_x: int,
    start_y: int,
    other_pieces: list[GamePiece],
    expected_moves: set[Point],
) -> None:
    """
    Test the legal moves for a piece

    :param piece_type: the type of the piece to test
    :param piece_x: the initial x position
    :param piece_y: the initial y position
    :param other_pieces: other pieces to place in the board
    :param expected_moves: what moves should the piece class find
    """

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


@pytest.mark.parametrize(
    "start_x, start_y, other_pieces, expected_moves",
    [
        (
            4,
            4,
            [],
            get_horizontal_moves(0, 4, 3)
            | get_horizontal_moves(5, 4, 9)
            | get_vertical_moves(4, 0, 3)
            | get_vertical_moves(4, 5, 9),
        ),
        (
            4,
            4,
            [
                # friendly piece
                GamePieceFactory.build(x=4, y=6),
                # enemy piece
                GamePieceFactory.build(color=enums.Color.BLACK, x=4, y=2),
            ],
            # fmt: off
            {
                Point(3, 4), Point(2, 4), Point(1, 4), Point(0, 4), # left
                Point(5, 4), Point(6, 4), Point(7, 4), Point(8, 4), Point(9, 4), # right
                Point(4, 5), # up, blocked by friendly piece
                Point(4, 3), Point(4, 2), # down, captures enemy piece
            }
            # fmt: on
        ),
        (
            9,
            9,
            [],
            {
                # up
                Point(9, 8),
                Point(9, 7),
                Point(9, 6),
                Point(9, 5),
                Point(9, 4),
                Point(9, 3),
                Point(9, 2),
                Point(9, 1),
                Point(9, 0),
                # left
                Point(8, 9),
                Point(7, 9),
                Point(6, 9),
                Point(5, 9),
                Point(4, 9),
                Point(3, 9),
                Point(2, 9),
                Point(1, 9),
                Point(0, 9),
            },
        ),
        (
            4,
            4,
            [
                GamePieceFactory.build(x=4, y=5),
                GamePieceFactory.build(x=4, y=3),
                GamePieceFactory.build(x=5, y=4),
                GamePieceFactory.build(x=3, y=4),
            ],
            set(),
        ),
    ],
    ids=[
        "in the center, nothing blocking",
        "in the center, blocked by friendly and enemy pieces",
        "in the corner (planning world domination)",
        "blocked by enemy pieces, no legal moves",
    ],
)
def test_rook(
    start_x: int,
    start_y: int,
    other_pieces: list[GamePiece],
    expected_moves: set[Point],
):
    assert_moves(
        enums.PieceType.ROOK,
        start_x,
        start_y,
        other_pieces,
        expected_moves,
    )


@pytest.mark.parametrize(
    "start_x, start_y, other_pieces, expected_moves",
    [
        (
            4,
            4,
            [],
            # fmt: off
            {
                Point(5, 3), Point(6, 2), Point(7, 1), Point(8, 0), # up right
                Point(3, 3), Point(2, 2), Point(1, 1), Point(0, 0), # up left
                Point(5, 5), Point(6, 6), Point(7, 7), Point(8, 8), Point(9, 9), # down right
                Point(3, 5), Point(2, 6), Point(1, 7), Point(0, 8), # down left
            }
            # fmt: on
        ),
    ],
    ids=[
        "in the center, nothing blocking",
    ],
)
def test_bishop(
    start_x: int,
    start_y: int,
    other_pieces: list[GamePiece],
    expected_moves: set[Point],
):
    assert_moves(
        enums.PieceType.BISHOP,
        start_x,
        start_y,
        other_pieces,
        expected_moves,
    )


# fmt: off
a = [
    [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0)],
    [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1), (9, 1)],
    [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2), (9, 2)],
    [(0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3), (9, 3)],
    [(0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4)],
    [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5)],
    [(0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6), (8, 6), (9, 6)],
    [(0, 7), (1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7), (9, 7)],
    [(0, 8), (1, 8), (2, 8), (3, 8), (4, 8), (5, 8), (6, 8), (7, 8), (8, 8), (9, 8)],
    [(0, 9), (1, 9), (2, 9), (3, 9), (4, 9), (5, 9), (6, 9), (7, 9), (8, 9), (9, 9)]
]
# fmt: on
