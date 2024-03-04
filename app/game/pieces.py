from abc import ABC

from app.models.games.game_piece_model import GamePiece
from app.game.board import Board
from app.constants import enums
from app.types import Offset, Point


class Piece(ABC):
    # how much to offset the position in each direction
    # to reach the points the piece could move to in a single move
    offsets: list[Offset] = []

    @classmethod
    def calc_legal_moves(cls, board: Board, position: Point) -> list[Point]:
        """
        Get a list of all the legal positions the piece can move to

        :param board: the chess board to scan
        :param position: the current position of the piece
        """

        legal_moves: list[Point] = []
        for offset in cls.offsets:
            legal_moves += cls._check_offset(board, position, offset)

        return legal_moves

    @classmethod
    def _check_offset(
        cls,
        board: Board,
        position: Point,
        offset: Offset,
    ) -> list[Point]:
        """
        Get a list of all the legal moves in a certain direction

        :param board: the chess board to scan
        :param position: the current position of the piece
        :param offset: the offset to add to the current position
        """

        curr_piece = board.get_piece(position)
        legal_moves: list[Point] = []
        while True:
            position += offset

            # Stop searching if out of bound
            if board.is_out_of_bound(position):
                break

            # Check if there is an uncapturable piece in the way
            can_capture = cls._can_capture(board, curr_piece, position)
            is_piece = board[position] is not None
            if is_piece and not can_capture:
                break

            legal_moves.append(position)

            # Is this the final time the piece can move in this direction?
            if not offset.slide or is_piece:
                break

        return legal_moves

    @staticmethod
    def _can_capture(
        board: Board,
        capturer: GamePiece,
        check_pos: Point,
    ) -> bool:
        captured = board[check_pos]
        return captured is not None and capturer.color != captured.color


class Queen(Piece):
    offsets = [
        Offset(1, 0),
        Offset(-1, 0),
        Offset(0, 1),
        Offset(0, -1),
        Offset(-1, 1),
        Offset(-1, -1),
        Offset(1, 1),
        Offset(1, -1),
    ]


class King(Piece):
    offsets = [
        Offset(1, 0, slide=False),
        Offset(-1, 0, slide=False),
        Offset(0, 1, slide=False),
        Offset(0, -1, slide=False),
        Offset(-1, 1, slide=False),
        Offset(-1, -1, slide=False),
        Offset(1, 1, slide=False),
        Offset(1, -1, slide=False),
    ]


class Rook(Piece):
    offsets = [Offset(1, 0), Offset(-1, 0), Offset(0, 1), Offset(0, -1)]


class Horsie(Piece):
    offsets = [
        Offset(1, 2, slide=False),
        Offset(1, -2, slide=False),
        Offset(-1, 2, slide=False),
        Offset(-1, -2, slide=False),
        Offset(2, 1, slide=False),
        Offset(2, -1, slide=False),
        Offset(-2, 1, slide=False),
        Offset(-2, -1, slide=False),
    ]


class Bishop(Piece):
    offsets = [Offset(-1, 1), Offset(-1, -1), Offset(1, 1), Offset(1, -1)]


PIECES: dict[enums.PieceType, type[Piece]] = {
    enums.PieceType.KING: King,
    enums.PieceType.QUEEN: Queen,
    enums.PieceType.ROOK: Rook,
    enums.PieceType.HORSIE: Horsie,
    enums.PieceType.BISHOP: Bishop,
}
