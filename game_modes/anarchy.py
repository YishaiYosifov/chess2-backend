import time

from flask_socketio import emit

import numpy

from dao import Game, User, Player, RatingArchive, AuthMethods
from util import SocketIOException, SocketIOErrors
from extensions import Square, PIECE_DATA, CONFIG
from app import db

class Anarchy:
    def __init__(self, game : Game): self.game = game

    def move(self, user : User, origin : dict, destination : dict, args):
        if user != self.game.turn: raise SocketIOException(SocketIOErrors.CONFLICT, "Wrong User")
        player : Player = self._get_player(user)

        # Check if both the origin and the destination squares are valid
        try:
            origin_square : Square = self.game.board[origin["y"], origin["x"]]
            destination_square : Square = self.game.board[destination["y"], destination["x"]]
            destination_piece = destination_square.piece
        except IndexError: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Squares")
        IS_CAPTURE = destination_square.piece != None

        # Check if the origin and destination squares are valid
        if not origin_square.piece or origin_square.piece.color != player.color: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Origin Square")

        # Get the movement of the piece
        piece_data : dict = PIECE_DATA[origin_square.piece.name]
        if not piece_data.get("allow_same_color_capture", False) and \
            IS_CAPTURE and \
            destination_square.piece.color == player.color: raise SocketIOException(SocketIOErrors.MOVE_ERROR, "Invalid Destination Square")

        collisions = piece_data.get("collisions")
        validator = piece_data.get("validate")
        if IS_CAPTURE:
            collisions = piece_data.get("collisions_capture") or collisions
            validator = piece_data.get("validate_capture") or validator
        
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
        self.game.moves.append(move_log)
        current_move_number = len(self.game.moves)

        if not move_log["moved"]:
            if IS_CAPTURE: move_log["captured"].append({"piece": destination_piece.name, "x": destination["x"], "y": destination["y"]})
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
            self.game.last_50_move_reset = current_move_number

        # Update the board and move history
        self.game.board[origin["y"], origin["x"]].piece = None
        self.game.legal_move_cache = {}
        db.session.query(Game).filter_by(game_id=self.game.game_id).update({"board": self.game.board})

        # 50 update move rule
        if move_log["captured"] or any("pawn" in moved["piece"] for moved in move_log["moved"]): self.game.last_50_move_reset = current_move_number

        if current_move_number - self.game.last_50_move_reset >= 100:
            # 50 move rule
            move_data["is_over"] = True
            self._end_game(0.5, 0.5, "50 Move Rule")
        else:
            # Check if the king was captured
            for square in move_log["captured"]:
                if square["piece"] == "king":
                    self._end_game(1 if player.color == "white" else 0, 1 if player.color == "black" else 0, "King Captured")
                    move_data["is_over"] = True
                    break

        # Update and sync the clock
        player.clock += self.game.game_settings.increment
        player.clock_synced_at = time.time()
        opponent.turn_started_at = time.time()
        self.sync_clock()

        # Cache all legal moves and hash the board for 3 fold repetition checking
        self.game.client_legal_move_cache = {}
        board_hash = []
        for row in self.game.board:
            board_hash.append([])
            for square in row:
                board_hash[-1].append(square.piece.name + square.piece.color if square.piece else "")
                if not square.piece: continue

                legal_moves = list(PIECE_DATA.get(square.piece.name)["all_legal"](self.game, {"x": square.x, "y": square.y}))
                if not legal_moves: continue

                self.game.client_legal_move_cache[str((square.x, square.y))] = list(
                    map(lambda move: {"x": move.x, "y": move.y}, legal_moves)
                )
            board_hash[-1] = tuple(board_hash[-1])
        board_hash = hash(tuple(board_hash))
        self.game.board_hashes.append(board_hash)
        if self.game.board_hashes.count(board_hash) >= 3:
            move_data["is_over"] = True
            self._end_game(0.5, 0.5, "3 Fold Repetition")

        move_data["legal_moves"] = self.game.client_legal_move_cache

        # Emit the move
        self.buffered_emit("move", move_data)

        self.game.turn = opponent
        db.session.commit()
    
    def resign(self, user : User): self._end_game(0 if user == self.game.white else 1, 0 if user == self.game.black else 1, "Resignation")

    # region Draw Management

    def request_draw(self, user : User):
        player : Player = self._get_player(user)
        if player.is_requesting_draw: raise SocketIOException(SocketIOErrors.BAD_REQUEST, "You already have an outgoing draw request")

        player.is_requesting_draw = True
        opponent = self._get_opponent(user)
        if not opponent.ignore_draw_requests: opponent.buffered_emit("draw_request")

        db.session.commit()

    def ignore_draw_requests(self, user : User):
        opponent = self._get_opponent(user)
        if not opponent.is_requesting_draw:
            raise SocketIOException(SocketIOErrors.BAD_REQUEST, "Opponent doesn't have outgoing draw requests")

        player : Player = self._get_player(user)
        player.ignore_draw_requests = True
        
        opponent.is_requesting_draw = False
        opponent.buffered_emit("draw_declined")

        db.session.commit()
    
    def decline_draw(self, user : User):
        opponent = self._get_opponent(user)
        if not opponent.is_requesting_draw:
            raise SocketIOException(SocketIOErrors.BAD_REQUEST, "Opponent doesn't have outgoing draw requests")

        opponent.is_requesting_draw = False
        opponent.buffered_emit("draw_declined")
        db.session.commit()
    
    def accept_draw(self, user : User):
        if not self._get_opponent(user).is_requesting_draw:
            raise SocketIOException(SocketIOErrors.BAD_REQUEST, "Opponent doesn't have outgoing draw requests")
        self._end_game(0.5, 0.5, "Agreement")

    # endregion
    
    def sync_clock(self):
        timestamp = time.time()
        
        is_timeout = False
        for player in [self.game.black, self.game.white]:
            if player != self.game.turn:
                player.clock += abs(time.time() - player.clock_synced_at)
                player.clock_synced_at = time.time()

            if player.clock <= timestamp:
                is_timeout = True
                if player == self.game.white: self._end_game(1, 0, "Timeout")
                else: self._end_game(0, 1, "Timeout")

        self.buffered_emit("clock_sync", {
                "white": self.game.white.clock,
                "black": self.game.black.clock,
                "is_timeout": is_timeout
            })
    
    def alert_stalling(self, user : User) -> bool:
        player : Player = self._get_player(user)

        stalling_timeout = CONFIG["STALL_TIMEOUTES"][str(int(self.game.game_settings.time_control / 60))] if len(self.game.moves) > 2 else CONFIG["FIRST_MOVES_STALL_TIMEOUT"]
        if not player.is_connected: stalling_timeout = min(stalling_timeout, CONFIG["DISCONNECTION_TIMEOUT"])
        if time.time() - player.turn_started_at < stalling_timeout: return

        if player == self.game.white: self._end_game(0, 1, "Game Abandoned")
        else: self._end_game(1, 0, "Game Abandoned")
    
    # region Helpers

    def _end_game(self, white_results : int, black_results : int, reason : str):
        if self.game.is_over: return

        updated_rows = Game.query.filter_by(game_id=self.game.game_id, is_over=False).update({"is_over": True})
        if updated_rows > 0: db.session.commit()
        else:
            db.session.rollback()
            return

        if len(self.game.moves) < 2:
            data = {
                "white_results": 0.5,
                "black_results": 0.5,
                "reason": "Aborted"
            }

            data["white_rating"] = self.game.white.user.rating(self.game.game_settings.mode).elo
            data["black_rating"] = self.game.black.user.rating(self.game.game_settings.mode).elo
            
            for delete in [self.game, self.game.white, self.game.black]: db.session.delete(delete)
        else:
            data = {
                "white_results": white_results,
                "black_results": black_results,
                "reason": reason
            }

            if self.game.white.user.auth_method == self.game.black.user.auth_method == AuthMethods.GUEST:
                data["white_rating"] = self.game.white.user.rating(self.game.game_settings.mode).elo
                data["black_rating"] = self.game.black.user.rating(self.game.game_settings.mode).elo
            else:
                data["white_rating"], data["black_rating"] = self._update_elo(white_results, black_results)

            self.game.ended_at = time.time()
    
            self.game.white.score = white_results
            self.game.black.score = black_results
            if self.game.match:
                self.game.match.white.score += white_results
                self.game.match.black.score += black_results
        
        self.buffered_emit("game_over", data)
        db.session.commit()

    def _get_player(self, user : User) -> Player: return self.game.white if user == self.game.white else self.game.black

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

    def buffered_emit(self, event : str, data : any):
        emit(event, data, to=self.game.token, namespace="/game")

        for player in [self.game.white, self.game.black]:
            if player.is_loading: player.buffered_loading_emits.append({"event": event, "data": data})
        db.session.commit()