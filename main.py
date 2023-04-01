import threading
import numpy
import flask
import time
import uuid
import os

from werkzeug.exceptions import HTTPException, BadRequest, Conflict, Unauthorized, NotFound, InternalServerError

from flask import redirect, session, render_template, send_from_directory
from flask_restful.reqparse import Argument

from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token

from pip._vendor import cachecontrol

from PIL import Image

import google.auth.transport.requests
import requests
import io

from dao.member import Member
from dao.auth import *

from frontend import frontend
from api import api

from util import *

app = flask.Flask(__name__)
app.secret_key = "bb5c8af0e15d4d0195e37fa995430280"

@app.route("/api/test", methods=["POST"])
def test():
    data = request.files["profile"]
    buffer = io.BytesIO(data.read())
    buffer.seek(0)
    
    image = Image.open(buffer)
    image = numpy.asarray(image)
    image = Image.fromarray(image).convert("RGB")

    image = image.resize((160, 160))
    image.save("static/uploads/test.jpeg")
    return "pog", 200

# region google auth

@app.route("/google_login_callback", methods=["GET"])
def google_signup():
    flow.fetch_token(authorization_response=request.url)
    if session["state"] != request.args["state"]: raise InternalServerError("State doesn't match")

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["session_token"] = uuid.uuid4().hex
    member = Member.select(email=id_info["email"])
    if member:
        member = member[0]
        member.session_token = session["session_token"]
        member.update()
    else: Member(session_token=session["session_token"], username=id_info["name"], email=id_info["email"], authentication_method=AuthenticationMethods.GMAIL).insert()
    
    session["alert"] = "Logged In Successfully"
    return redirect("/")

@app.route("/google_login", methods=["GET"])
def google_login():
    if "session_token" in session: return redirect("/")

    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

# endregion

@app.before_first_request
def start_clean_verifications():
    def clean_verifications():
        while True:
            for id, verification in awaiting_verification.copy().items():
                if verification["expires"] <= time.time(): awaiting_verification.pop(id)
            time.sleep(60)
    threading.Thread(target=clean_verifications).start()

@app.before_request
def permanent_session(): session.permanent = True

@app.errorhandler(HTTPException)
def http_error_handler(exception : HTTPException): return exception.description, exception.code

if __name__ == "__main__":
    flow = Flow.from_client_secrets_file(
        client_secrets_file="google_tokens/google_auth.json",
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
        redirect_uri="http://127.0.0.1:5000/google_login_callback"
    )
    
    app.register_blueprint(frontend)
    app.register_blueprint(api)

    app.run("0.0.0.0", debug=True)