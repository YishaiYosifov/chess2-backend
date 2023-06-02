import time

from flask_socketio import emit

import numpy

from util import SocketIOException, SocketIOErrors
from extensions import Square, PIECE_DATA, CONFIG
from dao import Game, User, Player, RatingArchive
from app import db

class Anarchy:
    def __init__(self, game : Game): self.game = game

    def move(self, user : User, origin : dict, destination : dict, args):
        self.game : Game = db.session.merge(self.game)
        if user != self.game.turn: raise SocketIOException(SocketIOErrors.CONFLICT, "Wrong User")
        player : Player = self.game.white if user == self.game.white else self.game.black

        # Check if both the origin and the destination squares are valid
        try:
            origin_square : Square = self.game.board[origin["y"], origin["x"]]
            destination_square : Square = self.game.board[destination["y"], destination["x"]]
        except IndexError: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Squares")
        IS_CAPTURE = destination_square.piece != None

        # Check if the origin and destination squares are valid
        if not origin_square.piece or origin_square.piece.color != player.color: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Origin Square")

        # Get the movement of the piece
        piece_data : dict = PIECE_DATA[origin_square.piece.name]
        if IS_CAPTURE and destination_square.piece.color == player.color: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Destination Square")

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
                if not square.piece or square.piece.color != player.color: continue

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
        move_data = {"move_log": move_log, "turn": opponent.color}
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
                self.end_game(1 if player.color == "white" else 0, 1 if player.color == "black" else 0, "King Captured")
                move_data["is_over"] = True
                break

        # Update and sync the clock
        player.clock += self.game.game_settings.increment
        player.clock_synced_since_last_turn_at = time.time()
        self.sync_clock()

        # Emit the move
        emit("move", move_data, to=self.game.token)

        self.game.turn = opponent
        db.session.commit()
    
    def end_game(self, white_results : int, black_results : int, reason : str):
        white_rating, black_rating = self._update_elo(white_results, black_results)
        emit("game_over", {"white_results": white_results, "black_results": black_results, "reason": reason, "white_rating": white_rating, "black_rating": black_rating}, to=self.game.token, namespace="/game")

        self.game.is_over = True
        self.game.ended_at = time.time()
        
        self.game.white.score = white_results
        self.game.black.score = black_results
        if self.game.match:
            self.game.match.white.score += white_results
            self.game.match.black.score += black_results
        db.session.commit()
    
    def sync_clock(self):
        timestamp = time.time()
        
        for player in [self.game.black, self.game.white]:
            if player != self.game.turn:
                player.clock += abs(time.time() - player.clock_synced_since_last_turn_at)
                player.clock_synced_since_last_turn_at = time.time()

            if player.clock <= timestamp:
                if player == self.game.white: self.end_game(1, 0, "Timeout")
                else: self.end_game(0, 1, "Timeout")
        emit("clock_sync", {
                "white": self.game.white.clock,
                "black": self.game.black.clock
            }, to=self.game.token, namespace="/game")
    
    # region Helpers

    def _get_opponent(self, user : User) -> Player:
        if user == self.game.white: return self.game.black
        else: return self.game.white

    def _update_elo(self, white_results : int, black_results : int) -> tuple[int, int]:
        white_rating = self.game.white.user.rating(self.game.game_settings.mode)
        black_rating = self.game.black.user.rating(self.game.game_settings.mode)

        white_expected = 1 / (1 + 10 ** ((black_rating.elo - white_rating.elo) / 400))
        black_expected = 1 - white_expected

        new_white_rating = RatingArchive(
            user=self.game.white.user,
            mode=self.game.game_settings.mode,
            elo=max(100, round(white_rating.elo + CONFIG["ELO_K_FACTOR"] * (white_results - white_expected)))
        )
        new_black_rating = RatingArchive(
            user=self.game.black.user,
            mode=self.game.game_settings.mode,
            elo=max(100, round(black_rating.elo + CONFIG["ELO_K_FACTOR"] * (black_results - black_expected)))
        )
        db.session.add_all([new_white_rating, new_black_rating])

        return new_white_rating.elo, new_black_rating.elo

    # endregion