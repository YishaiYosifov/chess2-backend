import time

from flask_socketio import disconnect, join_room, emit
from flask_restful.reqparse import Argument
from flask import request

from util import requires_auth, requires_args, socket_error_handler, SocketIOException, SocketIOErrors
from app import socketio, db
from dao import User

@socketio.on("connect", namespace="/game")
@requires_auth(allow_guests=True)
def game_connected(user : User):
    if not user.active_game:
        disconnect()
        return

    join_room(user.active_game.token)

    game_class = user.active_game.get_game_class()
    emit("opponent_connected", to=game_class._get_opponent(user).sid)

    player = game_class._get_player(user)
    if player.is_connected:
        emit("remote_connection", to=player.sid)
        disconnect(player.sid)

    player.sid = request.sid
    player.is_connected = True

    player.is_loading = False
    for buffered_emit in player.buffered_loading_emits: emit(buffered_emit["event"], buffered_emit["data"], to=player.sid, namespace="/game")
    player.buffered_loading_emits = []

    db.session.commit()
@socketio.on("disconnect", namespace="/game")
@requires_auth(allow_guests=True)
def game_disconnected(user : User):
    if not user.active_game: return

    game_class = user.active_game.get_game_class()
    player = game_class._get_player(user)
    player.is_connected = False
    player.disconnected_at = time.time()

    emit("opponent_disconnected", game_class._get_opponent(user).sid)
    db.session.commit()

@socketio.on("move", namespace="/game")
@socket_error_handler
@requires_auth(allow_guests=True)
@requires_args(
    Argument("origin_x", type=int, required=True), Argument("origin_y", type=int, required=True),
    Argument("destination_x", type=int, required=True), Argument("destination_y", type=int, required=True),
    Argument("promote_to", type=str, default=None)
)
def move(user : User, args):
    if not user.active_game: raise SocketIOException(SocketIOErrors.NOT_FOUND, "No Active Game")
    user.active_game.get_game_class().move(
        user,
        origin={"x": args.origin_x, "y": args.origin_y},
        destination={"x": args.destination_x, "y": args.destination_y},
        args=args
    )

@socket_error_handler
@requires_auth(allow_guests=True)
def basic_route(function_name, user : User):
    if not user.active_game: raise SocketIOException(SocketIOErrors.NOT_FOUND, "No Active Game")
    getattr(user.active_game.get_game_class(), function_name)(user)

BASIC_ROUTES = ["resign", "request_draw", "decline_draw", "accept_draw", "ignore_draw_requests"]
for route in BASIC_ROUTES: socketio.on(route, namespace="/game")(lambda route=route: basic_route(function_name=route))