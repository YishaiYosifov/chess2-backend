import threading
import flask
import time
import uuid

from werkzeug.exceptions import InternalServerError, Conflict

from flask import redirect, session, render_template, send_from_directory, jsonify
from flask_restful.reqparse import Argument

from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token

from pip._vendor import cachecontrol

import google.auth.transport.requests
import requests
import bcrypt

from dao.member import Member
from dao.auth import *

from util import *

app = flask.Flask(__name__)
app.secret_key = "bb5c8af0e15d4d0195e37fa995430280"

# region API

@app.route("/api/signup", methods=["POST"])
@requires_arguments(Argument("username", type=str, required=True), Argument("password", type=str, required=True), Argument("email", type=str, required=True))
def signup(args):
    username = args.username
    password = args.password
    email = args.email

    if len(username) > 60: raise BadRequest("Username Too Long")
    elif len(username) < 1: raise BadRequest("Username Too Short")
    
    if not STRONG_PASSWORD_REG.findall(password): raise BadRequest("Invalid Password")

    email_match = EMAIL_REG.match(email)
    if not email_match or email_match.group(0) != email: raise BadRequest("Invalid Email Address")

    if Member.select(email=email): raise Conflict("Email Taken")
    if Member.select(username=username): raise Conflict("Username Taken")
    
    Member(username=username, email=email, authentication_method=AuthenticationMethods.WEBSITE).insert()
    member_id = cursor.lastrowid

    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(password, salt)

    auth = WebsiteAuth(member_id=member_id, hash=hash, salt=salt)
    auth.insert()

    send_verification_email(email, auth)

    session["message"] = "Signed Up Successfully"
    return "Signed Up", 200

@app.route("/api/login", methods=["POST"])
@requires_arguments(Argument("selector", type=str, required=True), Argument("password", type=str, required=True))
def login(args):
    selector = args.selector
    password = args.password

    member : Member = Member.select(username=selector)
    if not member:
        member : Member = Member.select(email=selector)
        if not member: raise Unauthorized("Unknown email / username / password")
    member = member[0]
    
    if member.authentication_method != AuthenticationMethods.WEBSITE: raise BadRequest("Wrong Authorization Method")

    auth : WebsiteAuth = WebsiteAuth.select(member_id=member.member_id)[0]
    if bcrypt.hashpw(password, auth.salt) != auth.hash: raise Unauthorized("Unknown email / username / password")

    member.session_token = uuid.uuid4().hex
    member.update()
    session["session_token"] = member.session_token

    return "Logged In", 200

@app.route("/api/username_taken", methods=["POST"])
@requires_arguments(Argument("username", type=str, required=True))
def username_taken(args):
    if Member.select(username=args.username): return Conflict("Username Taken")
    return "Not Taken", 200

@app.route("/logout", methods=["POST", "GET"])
@requires_authentication(type=Member)
def logout(user : Member):
    session.pop("session_token")
    user.session_token = ""
    user.update()
    return redirect("/")

@app.route("/api/verify_email/<id>", methods=["GET"])
def verify_email(id):
    if not id in awaiting_verification:
        session["message"] = "Verification Link Expired"
        return redirect("/")

    auth : WebsiteAuth = awaiting_verification[id]["auth"]
    auth.verified = True
    auth.update()

    awaiting_verification.pop(id)

    session["message"] = "Email Verified"
    return redirect("/")

@app.route("/api/send_verification_email", methods=["POST"])
@requires_authentication(type=Member)
def send_verification_email_route(user : Member):
    auth : WebsiteAuth = WebsiteAuth.select(member_id=user.member_id)[0]
    if auth.verified: raise Conflict("Already Verified")

    send_verification_email(user.email, auth)
    return "Email Sent", 200

# endregion

# region google auth

@app.route("/google_login_callback", methods=["GET"])
def google_signup():
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
    
    session["message"] = "Logged In Successfully"
    return redirect("/")

@app.route("/google_login", methods=["GET"])
def google_login():
    if "session_token" in session: return redirect("/")

    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

# endregion

# region templates

@app.route("/")
def index_template():
    message = session.get("message")
    if message: session.pop("message")
    return render_template("index.html", message=message)

@app.route("/login")
def login_template():
    if "session_token" in session: return redirect("/")
    return render_template("login.html")

@app.route("/signup")
def signup_template():
    if "session_token" in session: return redirect("/")
    return render_template("signup.html")

@app.route("/play")
def play_template(): return render_template("play.html")

# endregion

# region assets

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static/assets"), "favicon.ico", mimetype="image/vnd.microsoft.icon")

# endregion

# region tests

@app.route("/protected")
@requires_authentication(type=Member)
def protected(user):
    print(user)
    return "Logged in!"

@app.route("/website_login_test")
def website_login_test():
    return """<script>
        fetch("http://127.0.0.1:5000/api/login", {
            method: "POST",
            body: JSON.stringify({"selector": "luka", "password": "ASdJAS48sddS"}),
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        });
    </script>""", 200

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

if __name__ == "__main__":
    flow = Flow.from_client_secrets_file(
        client_secrets_file="google_tokens/google_auth.json",
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
        redirect_uri="http://127.0.0.1:5000/google_login_callback"
    )

    app.run("0.0.0.0", debug=True)