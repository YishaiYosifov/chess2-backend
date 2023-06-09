from datetime import datetime, timedelta

import threading
import json
import time
import os

from werkzeug.exceptions import HTTPException, InternalServerError
from flask import redirect, session, request, make_response
from flask_socketio import emit

from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token

from pip._vendor import cachecontrol

import google.auth.transport.requests
import requests
import uuid

from frontend import frontend, TEMPLATES, default_template
from util import try_get_user_from_session, requires_auth
from extensions import GOOGLE_CLIENT_ID, CONFIG

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
        # If the email username is invalid, fix it / generate a new username
        username = id_info["name"].replace(" ", "")

        padding = uuid.uuid4().hex
        if len(username) < 3: username += padding[:4 - len(username)]
        if all(char.isdigit() for char in username): username = f"user-{padding[:5]}"

        while True:
            same_username = User.query.filter_by(username=username).first()
            if not same_username: break

            username = username[:25]
            username += uuid.uuid4()[:5]

        user = User(username=username, email=id_info["email"], auth_method=AuthMethods.GMAIL)
        user.insert()
    session["user_id"] = user.user_id
    db.session.commit()
    
    return redirect("/")

@app.route("/google_login", methods=["GET"])
def google_login():
    """
    Redirect the user to the google log in page
    """

    if try_get_user_from_session(force_logged_in=False): return redirect("/")

    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

# endregion

@socketio.on("connect")
@requires_auth(allow_guests=True)
def connected(user : User):
    user.sid = request.sid
    db.session.commit()

    if user.incoming_games: emit("incoming_games", [game.inviter_id for game in user.incoming_games])

# Delete expired columns
def delete_expired():
    while True:
        with app.app_context():
            now = datetime.utcnow()

            expired_guests : list[User] = User.query.filter(
                (User.last_accessed < (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")) &
                (User.auth_method == AuthMethods.GUEST)
            ).all()
            for user in expired_guests: user.delete()

            EmailVerification.query.filter(EmailVerification.created_at < (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")).delete()
            OutgoingGames.query.filter(OutgoingGames.created_at < (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")).delete()
            db.session.commit()

        time.sleep(60)

@app.errorhandler(HTTPException)
def http_error_handler(exception : HTTPException): return exception.description, exception.code

@app.after_request
def drop_response(response):
    new_response = make_response(response)

    if "text/html" in response.content_type:
        try: auth_info : dict = json.loads(request.cookies.get("auth_info"))
        except (ValueError, TypeError): auth_info = {}

        if not auth_info or auth_info.get("user_id") != session.get("user_id"):
            user = try_get_user_from_session(force_logged_in=False, allow_guests=True)
            new_response.set_cookie("auth_info", json.dumps(
                {
                    "user_id": user.user_id,
                    "auth_method": user.auth_method.value
                })
            )
    return new_response

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

    with app.app_context(): db.create_all()
    threading.Thread(target=delete_expired, daemon=True).start()

    socketio.run(app, "0.0.0.0", debug=CONFIG["DEBUG"], use_reloader=False)