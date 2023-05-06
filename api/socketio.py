from flask_socketio import emit
from flask import request

from util import requires_auth
from app import socketio, db
from dao import User

@socketio.on("connected")
@requires_auth(allow_guests=True)
def connected(user : User):
    user.sid = request.sid
    db.session.commit()

    if user.incoming_games: emit("incoming_games", [game.inviter_id for game in user.incoming_games])