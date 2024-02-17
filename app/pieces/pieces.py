from abc import ABC

from app.models.games import game_piece_model
from app.constants import constants
from app.types import Point

Board = dict[Point, game_piece_model.GamePiece]


class Piece(ABC):
    # whether the piece and move all the way in a certain direction or just once
    slide: bool = True

    # how much to offset the index each move
    offsets: list[Point] = []

    @classmethod
    def calc_legal_moves(cls, board: Board, position: Point):
        """
        Get a list of all the legal board indices the piece can move to

        :param board: the chess board to scan
        :param idx: the index of the piece
        """

        legal_moves: list[Point] = []
        curr_piece = board[position]

        for offset in cls.offsets:
            check_pos = position
            while True:
                check_pos.x += offset.x
                check_pos.y += offset.y

                # Out of bound
                if (
                    check_pos.y < 0
                    or check_pos.y >= constants.BOARD_HEIGHT
                    or check_pos.x < 0
                    or check_pos.x >= constants.BOARD_WIDTH
                ):
                    break

                # Check if there is an uncapturable piece in the way
                can_capture = cls.can_capture(board, curr_piece, check_pos)
                is_piece = board.get(check_pos) is not None
                if is_piece and not can_capture:
                    break

                legal_moves.append(check_pos)

                # Is this the final time the piece can move in this direction?
                if not cls.slide or is_piece:
                    break

        return legal_moves

    @staticmethod
    def can_capture(
        board: Board,
        capturer: game_piece_model.GamePiece,
        check_pos: Point,
    ) -> bool:
        captured = board.get(check_pos)
        return captured is not None and capturer.color != captured.color
