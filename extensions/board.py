from typing import Literal

from pydantic import BaseModel

import numpy

from . import CONFIG

class Piece(BaseModel):
    name : str
    color : Literal["white"] | Literal["black"]

    moved = False

class Square(BaseModel):
    piece : Piece = None

    x : int
    y : int

    def to_dict(self) -> dict:
        results = self.__dict__.copy()
        if self.piece: results["piece"] = self.piece.__dict__
        return results

# Initilize default board
SET_HEIGHT = len(CONFIG["PIECE_SET"])

parsed_pieces_white = numpy.empty((SET_HEIGHT, 8), Square)
parsed_pieces_black = numpy.empty((SET_HEIGHT, 8), Square)
for row_index, row in enumerate(CONFIG["PIECE_SET"]):
    for column_index, piece in enumerate(row):
        parsed_pieces_white[row_index][column_index] = Square(piece=Piece(name=piece, color="white") if piece else None, x=column_index, y=row_index)
        parsed_pieces_black[row_index][column_index] = Square(piece=Piece(name=piece, color="black") if piece else None, x=column_index, y=(SET_HEIGHT + 4) - row_index + 2)
parsed_pieces_black = parsed_pieces_black[::-1]

BOARD = numpy.concatenate((
    parsed_pieces_white,
    [[Square(x=column_index, y=SET_HEIGHT + row_index) for column_index in range(8)] for row_index in range(4)],
    parsed_pieces_black
))
BOARD_WIDTH, BOARD_HEIGHT = len(BOARD[0]), len(BOARD)