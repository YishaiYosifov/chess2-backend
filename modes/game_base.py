import threading
import time

from flask_socketio import emit
from util import SocketIOException, SocketIOErrors
from extensions import PIECE_MOVEMENT
from dao import Game, User, Piece
from app import app, db

class GameBase:
    def __init__(self, game : Game):
        self.game = game

        #threading.Thread(target=self._clock).start()

    def move(self, user, origin : dict, destination : dict):
        if user != self.game.turn: raise SocketIOException(SocketIOErrors.CONFLICT, "Wrong User")

        # Check if both the origin and the destination squares are valid
        try:
            origin_piece : Piece = self.game.board[origin["y"], origin["x"]]
            destination_piece : Piece = self.game.board[destination["y"], destination["x"]]
        except IndexError: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Squares")

        # Check if the origin and destination squares are valid
        user_color = self._get_color(user)
        if not origin_piece or origin_piece.color != user_color: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Origin Square")

        piece_data = PIECE_MOVEMENT[origin_piece.name]
        if destination_piece:
            if destination_piece.color == user_color: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Destination Square")
            move_check = piece_data.get("capture", piece_data["move"])
        else: move_check = piece_data["move"]        
        if not move_check(origin, destination): raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Move")

        self.game.board[destination["y"], destination["x"]] = origin_piece
        self.game.board[origin["y"], origin["x"]] = None

        #self.game.turn = self._get_opponent(user)

        db.session.merge(self.game)
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