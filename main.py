from datetime import datetime, timedelta

import threading
import time
import os

from werkzeug.exceptions import HTTPException, InternalServerError, Unauthorized

from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token

from pip._vendor import cachecontrol

from flask import redirect, session, request

import google.auth.transport.requests
import requests

from dao import LessThan, Member, AuthMethods, SessionToken, EmailVerification
from util import try_get_user_from_session, requires_auth, socketio_db

from frontend import frontend, TEMPLATES, default_template
from api import api

from extensions import GOOGLE_CLIENT_ID, CONFIG
from dao import PoolConn
from app import app, socketio

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
    member : Member = Member.select(email=id_info["email"]).first()
    if member: member.gen_session_token()
    else: Member(username=id_info["name"].replace(" ", ""), email=id_info["email"], auth_method=AuthMethods.GMAIL).insert()
    
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

# Delete expired columns
def delete_expired():
    while True:
        pool_conn = PoolConn()

        now = datetime.now()
        SessionToken.delete_all(pool_conn=pool_conn, last_used=LessThan((now - timedelta(weeks=2)).strftime("%Y-%m-%d %H:%M:%S")))
        EmailVerification.delete_all(pool_conn=pool_conn, created_at=LessThan((now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")))

        pool_conn.close()
        time.sleep(60)

@app.errorhandler(HTTPException)
def http_error_handler(exception : HTTPException):
    if request.path.split("/")[1] != "api":
        if isinstance(exception, Unauthorized):
            if exception.description == "Session Expired": return redirect("/login?a=session-expired")
            else: return redirect("/login")
    return exception.description, exception.code

@socketio.on("connected")
@socketio_db
@requires_auth()
def connected(user : Member):
    user.sid = request.sid
    user.update()

@app.before_request
def before_request():
    session.permanent = True
    request.pool_conn = PoolConn()
@app.teardown_request
def teardown_request(_):
    if hasattr(request, "pool_conn") and not request.pool_conn._closed: request.pool_conn.close()

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

    threading.Thread(target=delete_expired, daemon=True).start()

    socketio.run(app, "0.0.0.0", debug=CONFIG["debug"])