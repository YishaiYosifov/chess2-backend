from typing import Self
import re

from app.schemas.config_schema import CONFIG
from app.types import PieceInfo, Point
from app import enums


class Board:
    def __init__(
        self,
        board_width=CONFIG.board_width,
        board_height=CONFIG.board_height,
    ) -> None:
        self.board_width = board_width
        self.board_height = board_height
        self._board: dict[Point, PieceInfo] = {}

    @classmethod
    def from_fen(
        cls,
        fen: str,
        board_width: int = CONFIG.board_width,
        board_height: int = CONFIG.board_height,
    ) -> Self:
        board = cls(board_width, board_height)
        board._board = board._parse_fen(fen)
        return board

    def _parse_fen(self, fen: str) -> dict[Point, PieceInfo]:
        """
        Parse fen into a board

        :param fen: the fen to parse
        :return: a dictionary of the point and piece info of each piece
        """

        board: dict[Point, PieceInfo] = {}
        ranks = fen.split("/")
        # make sure the fen has the correct height
        if len(ranks) != self.board_height:
            raise ValueError(
                f"There are {len(ranks)} ranks, {self.board_height} necessary"
            )

        for y_coord, rank in enumerate(ranks):
            # split the rank into numbers and pieces.
            # this regex makes sure multiple digits are grouped together
            squares: list[str] = re.findall(r"[a-zA-Z]|\d+", rank)

            x_coord = 0
            for square in squares:
                # if the square is a digit, skip that amount of squares
                if square.isdigit():
                    x_coord += int(square)
                    continue

                color = (
                    enums.Color.WHITE if square.isupper() else enums.Color.BLACK
                )
                piece_type = enums.PieceType(square.lower())
                board[Point(x_coord, y_coord)] = PieceInfo(piece_type, color)
                x_coord += 1

            if x_coord != self.board_width:
                raise ValueError(
                    f"Rank {rank} has {x_coord} squares, {self.board_width} necessary"
                )

        return board

    def __setitem__(self, point: Point, piece: PieceInfo) -> None:
        if self.is_out_of_bound(point):
            raise ValueError(f"Point ({point.x}, {point.y}) is out of bound")

        self._board[point] = piece

    def __getitem__(self, point: Point) -> PieceInfo | None:
        return self._board.get(point)

    def get_piece(self, point: Point) -> PieceInfo:
        return self._board[point]

    def is_out_of_bound(self, point: Point):
        """Check if a point is out of the boundaries of the board"""

        return (
            point.x < 0
            or point.x >= self.board_width
            or point.y < 0
            or point.y >= self.board_height
        )
