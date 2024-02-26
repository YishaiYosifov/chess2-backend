from app.models.games.game_piece_model import GamePiece
from app.constants import constants
from app.types import Point


class Board:
    def __init__(
        self,
        pieces: list[GamePiece],
        board_width=constants.BOARD_WIDTH,
        board_height=constants.BOARD_WIDTH,
    ) -> None:
        self._board: dict[Point, GamePiece] = {}
        self._board_width = board_width
        self._board_height = board_height

        for piece in pieces:
            point = Point(piece.x, piece.y)
            # Raise an error if the piece is out of the provided board size
            if self.is_out_of_bound(point):
                raise ValueError(
                    f"{piece.color.value} {piece.piece.value}'s position is out of "
                    f"the boundaries of the board. "
                    f"(Board is {board_width}x{board_height}, piece is at {point})"
                )

            self._board[point] = piece

    def __getitem__(self, point: Point) -> GamePiece | None:
        return self._board.get(point)

    def get_piece(self, point: Point) -> GamePiece:
        return self._board[point]

    def is_out_of_bound(self, point: Point):
        """Check if a point is out of the boundaries of the board"""

        return (
            point.x < 0
            or point.x >= self._board_width
            or point.y < 0
            or point.y >= self._board_height
        )
