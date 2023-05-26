from datetime import datetime

import threading
import time

from flask_socketio import emit

import numpy

from util import SocketIOException, SocketIOErrors
from extensions import Square, PIECE_DATA, CONFIG
from dao import Match, Game, User
from app import app, db

class GameBase:
    def __init__(self, game : Game):
        self.game = game

        #threading.Thread(target=self._clock).start()

    def move(self, user : User, origin : dict, destination : dict, args):
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
        move_log = {"moved": [], "captured": []}
        if collisions:
            for collision in collisions:
                collision_results = collision(self.game, origin, destination)
                if isinstance(collision_results, dict):
                    success, move_log_portion = collision_results.get("success", False), collision_results.get("move_log_portion", [])
                    if not success: continue
                    move_log["captured"] += move_log_portion.get("captured", [])
                    move_log["moved"] += move_log_portion.get("moved", [])
                elif isinstance(collision_results, numpy.ndarray):
                    if len([square for square in collision_results if square.piece]) > 1: continue
                    self.game.board[destination["y"], destination["x"]].piece = origin_square.piece
                break
            else: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Collisions Failed")

        if not move_log["moved"]:
            if IS_CAPTURE: move_log["captured"].append({"piece": destination_square.piece.name, "x": destination["x"], "y": destination["y"]})
            move_log["moved"].append({"piece": origin_square.piece.name, "origin": origin, "destination": destination})
        if not collisions: self.game.board[destination["y"], destination["x"]].piece = origin_square.piece

        origin_square.piece.moved = True

        opponent = self._get_opponent(user)
        move_data = {"move_log": move_log, "turn": self._get_color(opponent)}
        if destination_square.piece and destination_square.piece.name == "pawn" and (destination_square.y == 0 or destination_square.y == len(self.game.board) - 1):
            if not args.promote_to: raise SocketIOException(SocketIOErrors.BAD_ARGUMENT, "Missing Argument: promote_to")
            elif "pawn" in args.promote_to or not args.promote_to in PIECE_DATA: raise SocketIOException(SocketIOErrors.PROMOTION_ERROR, "Invalid Promotion Piece")

            destination_square.piece.name = args.promote_to
            move_data["promote_to"] = args.promote_to

        # Update the board and move history
        self.game.moves.append(move_log)
        self.game.board[origin["y"], origin["x"]].piece = None
        self.game.legal_move_cache = {}
        db.session.query(Game).filter_by(game_id=self.game.game_id).update({"board": self.game.board, "moves": self.game.moves, "legal_move_cache": self.game.legal_move_cache})

        # Check if the king was taken
        for square in move_log["captured"]:
            if square["piece"] == "king":
                self.end_game(1 if user_color == "white" else -1, 1 if user_color == "black" else -1, "King Captured")
                move_data["is_over"] = True
                break

        # Emit the move and sync the clock
        emit("move", move_data, to=self.game.token)
        emit("clock_sync", self.game.clocks, to=self.game.token)

        self.game.turn = opponent
        db.session.commit()
    
    def end_game(self, white_results : int, black_results : int, reason : str):
        white_rating, black_rating = self.update_elo(white_results, black_results)
        emit("game_over", {"white_results": white_results, "black_results": black_results, "reason": reason, "white_rating": white_rating, "black_rating": black_rating}, to=self.game.token)

        self.game.is_over = True
        
        self.game.match.is_active = False
        self.game.match.last_game_over = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        self.game.match.white_results += white_results
        self.game.match.black_results += black_results
        db.session.commit()

    def update_elo(self, white_results : int, black_results : int) -> tuple[int, int]:
        white_rating = self.game.white.rating(self.game.game_settings.mode)
        black_rating = self.game.black.rating(self.game.game_settings.mode)

        white_expected = white_rating.elo / (white_rating.elo + black_rating.elo)
        black_expected = black_rating.elo / (white_rating.elo + black_rating.elo)

        if white_results == black_results == 0.5: k = CONFIG["DRAWN_ELO_K_FACTOR"]
        else: k = CONFIG["ELO_K_FACTOR"]

        white_rating.elo = round(white_rating.elo + k * (white_results * white_expected))
        black_rating.elo = round(black_rating.elo + k * (black_results * black_expected))

        return white_rating.elo, black_rating.elo
    
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