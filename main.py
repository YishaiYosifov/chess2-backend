from datetime import datetime, timedelta

import threading
import time
import os

from werkzeug.exceptions import HTTPException, InternalServerError, Unauthorized
from flask import redirect, session, request
from flask_socketio import emit, join_room

from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token

from pip._vendor import cachecontrol

import google.auth.transport.requests
import requests

from frontend import frontend, TEMPLATES, default_template
from util import try_get_user_from_session, requires_auth
from extensions import GOOGLE_CLIENT_ID, CONFIG

from game.game_base import GameBase
from app import app, socketio
from api import api
from dao import *

# region google auth

@app.route("/google_login_callback", methods=["GET"])
def google_signup():
    """
    This function will run when a user logs in using google.
    It gets their name and email address. If a user with the same email address exists, it will log them in. If it doesn't, it'll create a new account.
    """

    flow.fetch_token(authorization_response=request.url)
    if session["state"] != request.args["state"]: raise InternalServerError("State doesn't match")

    # Get credentials
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    # Generate the session token and log the user in
    user : User = User.query.filter_by(email=id_info["email"]).first()
    if not user:
        user = User(username=id_info["name"].replace(" ", ""), email=id_info["email"], auth_method=AuthMethods.GMAIL)
        user.insert()
    user.gen_session_token()
    db.session.commit()
    
    return redirect("/")

@app.route("/google_login", methods=["GET"])
def google_login():
    """
    Redirect the user to the google log in page
    """

    if try_get_user_from_session(must_logged_in=False, raise_on_session_expired=False): return redirect("/")

    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

# endregion

@socketio.on("connected")
@requires_auth(allow_guests=True)
def connected(user : User):
    user.sid = request.sid
    db.session.commit()

    if user.incoming_games: emit("incoming_games", [game.inviter_id for game in user.incoming_games])

@socketio.on("connect", namespace="/game")
@requires_auth(allow_guests=True)
def game_connected(user : User):
    game = user.get_active_game()
    if game: join_room(game.token)

# Delete expired columns
def delete_expired():
    while True:
        with app.app_context():
            now = datetime.utcnow()

            expired_guests : list[SessionToken] = SessionToken.query.filter(SessionToken.last_used < (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")) \
                .join(User).filter_by(auth_method=AuthMethods.GUEST).all()
            for guest in expired_guests: guest.user.delete()
            
            SessionToken.query.filter(SessionToken.last_used < (now - timedelta(weeks=2)).strftime("%Y-%m-%d %H:%M:%S")).delete()
            EmailVerification.query.filter(EmailVerification.created_at < (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")).delete()
            OutgoingGames.query.filter(OutgoingGames.created_at < (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")).delete()
            db.session.commit()

        time.sleep(60)

@app.errorhandler(HTTPException)
def http_error_handler(exception : HTTPException):
    if request.path.split("/")[1] != "api":
        if isinstance(exception, Unauthorized):
            if exception.description == "Session Expired": return redirect("/login?a=session-expired")
            else: return redirect("/login")
    return exception.description, exception.code

if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Gmail Auth
    flow = Flow.from_client_secrets_file(
        client_secrets_file="google_tokens/google_auth.json",
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
        redirect_uri="http://127.0.0.1:5000/google_login_callback"
    )
    
    # Register templates
    for template in TEMPLATES:
        route = lambda template=template, **kwargs: default_template(template, **kwargs)
        route.__name__ = template.route
        app.route(template.route)(route)

    # Register blueprints
    app.register_blueprint(frontend)
    app.register_blueprint(api)

    with app.app_context():
        db.create_all()

        for active_game in Game.query.all(): active_games[active_game.token] = GameBase(active_game)
    threading.Thread(target=delete_expired, daemon=True).start()

    socketio.run(app, "0.0.0.0", debug=CONFIG["DEBUG"], use_reloader=False)