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
BOARD_STARTING_MOVES = {
    "(1, 0)": [{"x": 2, "y": 2}],
    "(6, 0)": [{"x": 5, "y": 2}],
    "(1, 1)": [{"x": 3, "y": 2}, {"x": 2, "y": 3}, {"x": 0, "y": 3}],
    "(2, 1)": [{"x": 2, "y": 2}, {"x": 2, "y": 3}],
    "(3, 1)": [{"x": 3, "y": 2}, {"x": 3, "y": 3}, {"x": 3, "y": 4}],
    "(4, 1)": [{"x": 4, "y": 2}, {"x": 4, "y": 3}, {"x": 4, "y": 4}],
    "(5, 1)": [{"x": 5, "y": 2}, {"x": 5, "y": 3}],
    "(6, 1)": [{"x": 7, "y": 3}, {"x": 5, "y": 3}, {"x": 4, "y": 2}],
    "(0, 2)": [{"x": 0, "y": 4}, {"x": 0, "y": 6}],
    "(1, 2)": [{"x": 1, "y": 3}, {"x": 1, "y": 4}],
    "(6, 2)": [{"x": 6, "y": 3}, {"x": 6, "y": 4}],
    "(7, 2)": [{"x": 7, "y": 4}, {"x": 7, "y": 6}],
    "(0, 7)": [{"x": 0, "y": 5}, {"x": 0, "y": 3}],
    "(1, 7)": [{"x": 1, "y": 6}, {"x": 1, "y": 5}],
    "(6, 7)": [{"x": 6, "y": 6}, {"x": 6, "y": 5}],
    "(7, 7)": [{"x": 7, "y": 5}, {"x": 7, "y": 3}],
    "(1, 8)": [{"x": 3, "y": 7}, {"x": 2, "y": 6}, {"x": 0, "y": 6}],
    "(2, 8)": [{"x": 2, "y": 7}, {"x": 2, "y": 6}],
    "(3, 8)": [{"x": 3, "y": 7}, {"x": 3, "y": 6}, {"x": 3, "y": 5}],
    "(4, 8)": [{"x": 4, "y": 7}, {"x": 4, "y": 6}, {"x": 4, "y": 5}],
    "(5, 8)": [{"x": 5, "y": 7}, {"x": 5, "y": 6}],
    "(6, 8)": [{"x": 7, "y": 6}, {"x": 5, "y": 6}, {"x": 4, "y": 7}],
    "(1, 9)": [{"x": 2, "y": 7}],
    "(6, 9)": [{"x": 5, "y": 7}]
}