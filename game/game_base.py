import threading
import time

from flask_socketio import emit

from util import SocketIOException, SocketIOErrors
from game.pieces import PIECE_MOVEMENT
from dao import Game, User, Piece
from app import app, db

class GameBase:
    def __init__(self, game : Game):
        self.game = game

        #threading.Thread(target=self._clock).start()

    def move(self, user, origin : dict, destination : dict):
        self.game = db.session.merge(self.game)
        if user != self.game.turn: raise SocketIOException(SocketIOErrors.CONFLICT, "Wrong User")

        # Check if both the origin and the destination squares are valid
        try:
            origin_piece : Piece = self.game.board[origin["y"], origin["x"]]
            destination_piece : Piece = self.game.board[destination["y"], destination["x"]]
        except IndexError: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Squares")

        # Check if the origin and destination squares are valid
        user_color = self._get_color(user)
        if not origin_piece or origin_piece.color != user_color: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Origin Square")

        # Get the movement of the piece
        piece_data = PIECE_MOVEMENT[origin_piece.name]
        if destination_piece:
            if destination_piece.color == user_color: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Destination Square")
            move_check = piece_data.get("capture", piece_data["move"])
        else: move_check = piece_data["move"]
        # Check if the given move is possible
        if not move_check["validator"](self.game.board, origin, destination): raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Move")

        # Check if there are any pieces in the way
        if move_check.get("collisions"):
            for collision_check in move_check["collisions"]:
                collision = collision_check(self.game.board, origin, destination)
                if len([square for square in collision if square]) <= 1: break
            else: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Collisions Failed")

        # Move the piece to the new position and replace the old piece
        self.game.board[destination["y"], destination["x"]] = origin_piece
        self.game.board[origin["y"], origin["x"]] = None
        origin_piece.moved += 1

        # Looks bad but I have to do this to make sqlalchemy update the board
        self.game.board = self.game.board

        emit("move", {"origin": origin, "destination": destination}, include_self=False, to=self.game.token)

        self.game.turn = self._get_opponent(user)
        db.session.commit()
    
    # region Helpers

    def _get_opponent(self, user : User) -> User:
        if user == self.game.white: return self.game.black
        else: return self.game.white
    def _get_color(self, user : User) -> User: return "white" if user == self.game.white else "black"

    # endregion

    def _clock(self):
        while True:
            self.game.clocks[self.game.turn.user_id] -= 0.1
            if self.game.clocks[self.game.turn.user_id] <= 0:
                with app.app_context(): emit("game_over", {"winner": self.game.turn.user_id, "reason": "Timeout"}, namespace="/game", room=self.game.token)
                return
            time.sleep(0.1)