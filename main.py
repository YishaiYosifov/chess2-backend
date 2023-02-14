import flask

from werkzeug.exceptions import InternalServerError, NotImplemented

from flask_restful.reqparse import Argument
from flask import redirect, session

from pip._vendor import cachecontrol

from google.oauth2 import id_token

import google.auth.transport.requests
import requests
import uuid

from dao.member import *
from util import *

app = flask.Flask(__name__)
app.secret_key = "bb5c8af0e15d4d0195e37fa995430280"

@app.route("/api/register", methods=["POST"])
@requires_arguments(Argument("username", type=str, required=True), Argument("password", type=str, required=True), Argument("email", type=str, required=True))
def register(args): raise NotImplemented

@app.route("/api/login", methods=["POST"])
@requires_arguments(Argument("username", type=str, required=True), Argument("password", type=str, required=True), Argument("email", type=str, required=True))
def login(args): raise NotImplemented

@app.route("/google_login_callback", methods=["GET"])
def google_register():
    flow.fetch_token(authorization_response=request.url)
    if session["state"] != request.args["state"]: raise InternalServerError()

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

    return redirect("/")

@app.route("/google_login", methods=["GET"])
def test():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/protected")
@requires_authentication(type=Member)
def protected(user):
    print(user)
    return "Logged in!"

if __name__ == "__main__": app.run("0.0.0.0", debug=True)