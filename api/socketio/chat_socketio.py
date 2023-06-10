from flask_socketio import disconnect, join_room, emit
from werkzeug.exceptions import NotFound, BadRequest
from flask_restful.reqparse import Argument

from util import requires_auth, requires_args, socket_error_handler
from app import socketio
from dao import User

@socketio.on("connect", namespace="/chat")
@requires_auth(allow_guests=True)
def chat_connected(user : User):
    if not user.active_game:
        disconnect()
        return
    join_room(user.active_game.token)

@socketio.on("send_message", namespace="/chat")
@socket_error_handler
@requires_auth(allow_guests=True)
@requires_args(Argument("message", type=str))
def send_message(user : User, args):
    if not user.active_game: raise NotFound("No Active Game")
    if not len(args.message) in range(1, 150): raise BadRequest("Invalid Message Length")

    emit("new_message", args.message, to=user.active_game.token, namespace="/chat")
    return "Message Sent", 200