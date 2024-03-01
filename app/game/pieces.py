from abc import ABC

from app.models.games.game_piece_model import GamePiece
from app.game.board import Board
from app.constants import enums
from app.types import Point


class Piece(ABC):
    # whether the piece and move all the way in a certain direction or just once
    slide: bool = True

    # how much to offset the index each move
    offsets: list[Point] = []

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
        offset: Point,
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
            if not cls.slide or is_piece:
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


class Rook(Piece):
    offsets = [Point(1, 0), Point(-1, 0), Point(0, 1), Point(0, -1)]


class Bishop(Piece):
    offsets = [Point(-1, 1), Point(-1, -1), Point(1, 1), Point(1, -1)]


PIECES: dict[enums.PieceType, type[Piece]] = {
    enums.PieceType.ROOK: Rook,
    enums.PieceType.BISHOP: Bishop,
}
