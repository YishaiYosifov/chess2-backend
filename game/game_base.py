import threading
import time

from flask_socketio import emit

import numpy

from util import SocketIOException, SocketIOErrors
from game.pieces import PIECE_DATA
from dao import Game, User, Square
from app import app, db

class GameBase:
    def __init__(self, game : Game):
        self.game = game

        #threading.Thread(target=self._clock).start()

    def move(self, user, origin : dict, destination : dict):
        self.game : Game = db.session.merge(self.game)
        if user != self.game.turn: raise SocketIOException(SocketIOErrors.CONFLICT, "Wrong User")

        # Check if both the origin and the destination squares are valid
        try:
            origin_square : Square = self.game.board[origin["y"], origin["x"]]
            destination_square : Square = self.game.board[destination["y"], destination["x"]]
        except IndexError: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Squares")
        IS_CAPTURE = destination_square.piece != None

        # Check if the origin and destination squares are valid
        user_color = self._get_color(user)
        if not origin_square.piece or origin_square.piece.color != user_color: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Origin Square")

        # Get the movement of the piece
        piece_data : dict = PIECE_DATA[origin_square.piece.name]
        if IS_CAPTURE and destination_square.piece.color == user_color: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Destination Square")

        if IS_CAPTURE:
            collisions = piece_data.get("collisions_capture")
            validator = piece_data.get("validate_capture")
        else:
            collisions = piece_data.get("collisions")
            validator = piece_data.get("validate")
        
        # Forced moves
        max_forced = {"priority": 0}
        max_forced_priority_played = 0
        for row in self.game.board:
            for square in row:
                if not square.piece or square.piece.color != user_color: continue

                for find_forced, priority in PIECE_DATA[square.piece.name].get("forced", {}).items():
                    forced_results, moves = find_forced(self.game, square, origin, destination)
                    if not forced_results: continue
                    elif forced_results == 2 and max_forced_priority_played < priority: max_forced_priority_played = priority

                    if max_forced["priority"] < priority: max_forced = {"priority": priority, "moves": moves}
                    elif max_forced["priority"] == priority: max_forced["moves"] += moves
        if max_forced["priority"] > max_forced_priority_played: raise SocketIOException(SocketIOErrors.FORCED_MOVE_ERROR, max_forced["moves"])

        # Check if the move is possible
        if validator and not validator(self.game, origin, destination): raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Move")

        # Process the move
        origin_square.piece.moved = True
        if collisions:
            for collision in collisions:
                sliced = collision(self.game, origin, destination)
                if isinstance(sliced, bool) and not sliced: continue
                elif isinstance(sliced, numpy.ndarray):
                    if len([square for square in sliced if square.piece]) > 1: continue
                    self.game.board[destination["y"], destination["x"]].piece = origin_square.piece
                break
            else: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Collisions Failed")
        else: self.game.board[destination["y"], destination["x"]].piece = origin_square.piece

        # Update the board and move history
        self.game.moves.append({"piece": origin_square.piece.name, "origin": origin, "destination": destination})
        self.game.board[origin["y"], origin["x"]].piece = None
        db.session.query(Game).filter_by(game_id=self.game.game_id).update({"board": self.game.board, "moves": self.game.moves})

        # Emit the move and sync the clock
        opponent = self._get_opponent(user)
        emit("move", {"origin": origin, "destination": destination, "turn": self._get_color(opponent)}, to=self.game.token)
        emit("clock_sync", self.game.clocks, to=self.game.token)

        self.game.turn = opponent
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