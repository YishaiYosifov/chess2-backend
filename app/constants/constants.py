from app.schemas import game_schema

from . import enums

BOARD_WIDTH = 10
BOARD_HEIGHT = 10

# fmt: off

STARTING_POSITION: list[game_schema.Piece] = [
    game_schema.Piece(piece=enums.Piece.ROOK, color=enums.Color.WHITE, x=0, y=0),
    game_schema.Piece(piece=enums.Piece.HORSE, color=enums.Color.WHITE, x=1, y=0),
    game_schema.Piece(piece=enums.Piece.KNOOK, color=enums.Color.WHITE, x=2, y=0),
    game_schema.Piece(piece=enums.Piece.XOOK, color=enums.Color.WHITE, x=3, y=0),
    game_schema.Piece(piece=enums.Piece.QUEEN, color=enums.Color.WHITE, x=4, y=0),
    game_schema.Piece(piece=enums.Piece.KING, color=enums.Color.WHITE, x=5, y=0),
    game_schema.Piece(piece=enums.Piece.BISHOP, color=enums.Color.WHITE, x=6, y=0),
    game_schema.Piece(piece=enums.Piece.ANTIQUEEN, color=enums.Color.WHITE, x=7, y=0),
    game_schema.Piece(piece=enums.Piece.HORSE, color=enums.Color.WHITE, x=8, y=0),
    game_schema.Piece(piece=enums.Piece.ROOK, color=enums.Color.WHITE, x=9, y=0),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, x=0, y=1),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, x=1, y=1),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.WHITE, x=2, y=1),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, x=3, y=1),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.WHITE, x=4, y=1),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.WHITE, x=5, y=1),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, x=6, y=1),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.WHITE, x=7, y=1),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, x=8, y=1),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.WHITE, x=9, y=1),
    game_schema.Piece(piece=enums.Piece.ARCHBISHOP, color=enums.Color.WHITE, x=0, y=2),
    game_schema.Piece(piece=enums.Piece.ARCHBISHOP, color=enums.Color.WHITE, x=9, y=2),

    game_schema.Piece(piece=enums.Piece.ARCHBISHOP, color=enums.Color.BLACK, x=9, y=7),
    game_schema.Piece(piece=enums.Piece.ARCHBISHOP, color=enums.Color.BLACK, x=0, y=7),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, x=9, y=8),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, x=8, y=8),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.BLACK, x=7, y=8),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, x=6, y=8),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.BLACK, x=5, y=8),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.BLACK, x=4, y=8),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, x=3, y=8),
    game_schema.Piece(piece=enums.Piece.PAWN, color=enums.Color.BLACK, x=2, y=8),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, x=1, y=8),
    game_schema.Piece(piece=enums.Piece.CHILD_PAWN, color=enums.Color.BLACK, x=0, y=8),
    game_schema.Piece(piece=enums.Piece.ROOK, color=enums.Color.BLACK, x=9, y=9),
    game_schema.Piece(piece=enums.Piece.HORSE, color=enums.Color.BLACK, x=8, y=9),
    game_schema.Piece(piece=enums.Piece.ANTIQUEEN, color=enums.Color.BLACK, x=7, y=9),
    game_schema.Piece(piece=enums.Piece.BISHOP, color=enums.Color.BLACK, x=6, y=9),
    game_schema.Piece(piece=enums.Piece.KING, color=enums.Color.BLACK, x=5, y=9),
    game_schema.Piece(piece=enums.Piece.QUEEN, color=enums.Color.BLACK, x=4, y=9),
    game_schema.Piece(piece=enums.Piece.XOOK, color=enums.Color.BLACK, x=3, y=9),
    game_schema.Piece(piece=enums.Piece.KNOOK, color=enums.Color.BLACK, x=2, y=9),
    game_schema.Piece(piece=enums.Piece.HORSE, color=enums.Color.BLACK, x=1, y=9),
    game_schema.Piece(piece=enums.Piece.ROOK, color=enums.Color.BLACK, x=0, y=9),
]

# fmt: on
