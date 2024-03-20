from dataclasses import dataclass, field
from abc import ABC

from app.schemas.game_schema import MoveMetadata
from app.game.board import Board
from app.types import PieceInfo, Offset, Point
from app import enums


@dataclass
class PieceMoves:
    moves: dict[Point, MoveMetadata] = field(default_factory=dict)
    ghosts: dict[Point, Point] = field(default_factory=dict)

    def merge_moves(self, legal_moves: "PieceMoves") -> None:
        self.moves.update(legal_moves.moves)
        self.ghosts.update(legal_moves.ghosts)


class Piece(ABC):
    # how much to offset the position in each step
    # to reach the points the piece could move to in a single move
    offsets: list[Offset] = []

    @classmethod
    def calc_legal_moves(cls, board: Board, position: Point) -> PieceMoves:
        """
        Get a list of all the legal positions the piece can move to

        :param board: the chessboard to scan
        :param position: the current position of the piece
        """

        legal_moves = PieceMoves()
        for offset in cls.offsets:
            moves = cls._check_offset(board, position, offset)
            legal_moves.merge_moves(moves)

        return legal_moves

    @classmethod
    def _check_offset(
        cls,
        board: Board,
        position: Point,
        offset: Offset,
    ) -> PieceMoves:
        """
        Get a list of all the legal moves in a certain direction

        :param board: the chessboard to scan
        :param position: the current position of the piece
        :param offset: the offset to add to the current position

        :return: every point the piece could go to and its metadata
        """

        curr_piece = board.get_piece(position)
        legal_moves = PieceMoves()
        while True:
            position += offset

            # stop searching if out of bound
            if board.is_out_of_bound(position):
                break

            can_capture = (
                cls.can_capture(board, curr_piece, position)
                and offset.can_capture
            )
            is_piece = board[position] is not None

            # check if there is an uncapturable piece in the way
            if is_piece and not can_capture:
                break

            legal_moves.moves[position] = MoveMetadata(is_capture=is_piece)

            # is this the final time the piece can move in this direction?
            if not offset.slide or is_piece:
                break

        return legal_moves

    @staticmethod
    def can_capture(
        board: Board,
        capturer: PieceInfo,
        captured_pos: Point,
    ) -> bool:
        captured = board[captured_pos]
        return captured is not None and capturer.color != captured.color


# region Piece Implementation


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

    # king x position, rook x position
    short_castle_x: tuple[int, int] = (8, 7)
    long_castle_x: tuple[int, int] = (2, 3)

    @classmethod
    def calc_legal_moves(cls, board: Board, position: Point) -> PieceMoves:
        legal_moves = super().calc_legal_moves(board, position)

        # find castling moves
        legal_moves.merge_moves(
            cls.castle(
                board,
                position,
                Point(0, position.y),
            )
        )

        legal_moves.merge_moves(
            cls.castle(
                board,
                position,
                Point(board.board_width - 1, position.y),
            )
        )

        return legal_moves

    @classmethod
    def castle(
        cls,
        board: Board,
        king_pos: Point,
        rook_pos: Point,
    ) -> PieceMoves:
        """
        Perform castling move if possible

        :param board: the chessboard
        :param king_pos: the position of the king
        :param rook_pos: the position of the potential rook to castle with

        :return: the castling moves if found, an empty dictionary otherwise
        """

        if not cls.can_castle_with(board, king_pos, rook_pos):
            return PieceMoves()

        if rook_pos.x < king_pos.x:
            king_x, rook_x = cls.long_castle_x
            ghost_range = range(rook_pos.x + 1, king_pos.x - 1)
        else:
            king_x, rook_x = cls.short_castle_x
            ghost_range = range(king_pos.x + 2, rook_pos.x)

        king_dest = Point(king_x, king_pos.y)
        rook_dest = Point(rook_x, rook_pos.y)

        # all the points between the king and the rook should be clickable,
        # but redirect to the actual point
        ghost_moves = {
            Point(x, king_pos.y): king_dest
            for x in ghost_range
            if x != king_dest.x
        }

        moves = PieceMoves(
            moves={
                king_dest: MoveMetadata(
                    notation_type=enums.NotationType.CASTLE,
                    side_effect_moves={rook_pos: rook_dest},
                )
            },
            ghosts=ghost_moves,
        )

        return moves

    @staticmethod
    def can_castle_with(
        board: Board,
        king_pos: Point,
        castle_with_pos: Point,
    ) -> bool:
        """
        Determine whether castling is possible with a given rook

        :param board: the chessboard
        :param king_pos: the position of the king
        :param castle_with_pos: the position of the rook with whom to castle with

        :return: true if possible, false otherwise
        """

        castle_with = board[castle_with_pos]

        is_path_blocked = any(
            Point(x, king_pos.y) in board
            for x in range(king_pos.x + 1, castle_with_pos.x)
        )

        is_long = castle_with_pos.x < king_pos.x
        has_castling_rights = (is_long and board.castle_rights_long) or (
            not is_long and board.castle_rights_short
        )

        return (
            not is_path_blocked
            and has_castling_rights
            # same rank
            and castle_with_pos.y == king_pos.y
            # correct piece type
            and castle_with is not None
            and castle_with.piece_type == enums.PieceType.ROOK
        )


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


class Knook(Piece):
    offsets = [
        # rook moves
        Offset(1, 0, can_capture=False),
        Offset(-1, 0, can_capture=False),
        Offset(0, 1, can_capture=False),
        Offset(0, -1, can_capture=False),
        # horsie moves
        Offset(1, 2, slide=False),
        Offset(1, -2, slide=False),
        Offset(-1, 2, slide=False),
        Offset(-1, -2, slide=False),
        Offset(2, 1, slide=False),
        Offset(2, -1, slide=False),
        Offset(-2, 1, slide=False),
        Offset(-2, -1, slide=False),
    ]


class Archbishop(Piece):
    # move like a rook, but can only go on the same color square
    offsets = [Offset(2, 0), Offset(-2, 0), Offset(0, 2), Offset(0, -2)]


class Xook(Piece):
    offsets = [
        # move like a bishop
        Offset(-1, 1),
        Offset(-1, -1),
        Offset(1, 1),
        Offset(1, -1),
        # but one square straight
        Offset(1, 0, slide=False),
        Offset(-1, 0, slide=False),
        Offset(0, 1, slide=False),
        Offset(0, -1, slide=False),
    ]


# endregion

PIECES: dict[enums.PieceType, type[Piece]] = {
    enums.PieceType.KING: King,
    enums.PieceType.QUEEN: Queen,
    enums.PieceType.ROOK: Rook,
    enums.PieceType.HORSIE: Horsie,
    enums.PieceType.BISHOP: Bishop,
    enums.PieceType.KNOOK: Knook,
    enums.PieceType.ARCHBISHOP: Archbishop,
    enums.PieceType.XOOK: Xook,
}
