from abc import ABC

from app.models.games import game_piece_model
from app.constants import constants
from app.types import Board


class Piece(ABC):
    # whether the piece and move all the way in a certain direction or just once
    slide: bool = True

    # how much to offset the index each move
    offsets: list[int] = []

    @classmethod
    def calc_legal_moves(
        cls,
        board: Board,
        idx: int,
    ):
        """
        Get a list of all the legal board indices the piece can move to

        :param board: the chess board to scan
        :param idx: the index of the piece
        """

        legal_moves: list[int] = []
        curr_piece = board[idx]

        for offset in cls.offsets:
            check_idx = idx
            while True:
                check_idx += offset

                # Out of bound
                if constants.MAILBOX[check_idx] == -1:
                    break

                # Check if there is an uncapturable piece in the way
                can_capture = cls.can_capture(board, curr_piece, check_idx)
                is_piece = board.get(check_idx) is not None
                if is_piece and not can_capture:
                    break

                legal_moves.append(check_idx)

                # Is this the final time the piece can move in this direction?
                if not cls.slide or is_piece:
                    break

        return legal_moves

    @staticmethod
    def can_capture(
        board: Board,
        capturer: game_piece_model.GamePiece,
        check_idx: int,
    ) -> bool:
        captured = board.get(check_idx)
        return captured is not None and capturer.color != captured.color
