import threading
import flask
import time
import uuid

from werkzeug.exceptions import HTTPException, BadRequest, Conflict, Unauthorized, NotFound, InternalServerError

from flask import redirect, session, render_template, send_from_directory
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

    if Member.select(username=username): raise Conflict("Username Taken")
    if Member.select(email=email): raise Conflict("Email Taken")
    
    Member(username=username, email=email, authentication_method=AuthenticationMethods.WEBSITE).insert()
    member_id = cursor.lastrowid

    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(password, salt)

    auth = WebsiteAuth(member_id=member_id, hash=hash, salt=salt)
    auth.insert()

    send_verification_email(email, auth)

    session["alert"] = "Signed Up Successfully"
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

@app.route("/logout", methods=["POST", "GET"])
@requires_authentication(type=Member)
def logout(user : Member):
    session.clear()
    user.session_token = ""
    user.update()
    return redirect("/")

@app.route("/api/verify_email/<user_id>/<id>", methods=["GET"])
def verify_email(user_id, id):
    user_id = int(user_id)
    verification_data = awaiting_verification.get(user_id)
    if not verification_data or verification_data["id"] != id:
        session["alert"] = "Verification Link Expired"
        return redirect("/")

    auth : WebsiteAuth = verification_data["auth"]
    auth.verified = True
    auth.update()

    awaiting_verification.pop(user_id)

    session["alert"] = "Email Verified!"
    return redirect("/")

@app.route("/api/send_verification_email", methods=["POST"])
@requires_authentication(type=Member)
def send_verification_email_route(user : Member):
    auth : WebsiteAuth = WebsiteAuth.select(member_id=user.member_id)[0]
    if auth.verified: raise Conflict("Already Verified")

    send_verification_email(user.email, auth)
    return "Email Sent", 200

@app.route("/api/get_user_info", methods=["POST"])
@requires_arguments(Argument("username", default=None, type=str, required=False))
def get_user_info(args):
    if args.username:
        user : Member = Member.select(username=args.username)
        if not user: raise NotFound("User Not Found")
        user = user[0]
    else:
        try: user : Member = get_user_from_session()
        except Unauthorized as e:
            if e.description == "Not Logged In": raise BadRequest("Username not given and not logged in")
            raise
    
    print(user)
    return user.get_public_info(), 200

@app.route("/api/get_personal_info", methods=["POST"])
@requires_authentication(type=Member)
def get_personal_info(user : Member):
    session["session_token"] = "abc"
    return "ok", 200

# endregion

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

# region templates

@app.route("/")
def index_template():
    alert = session.get("alert")
    if alert: session.pop("alert")
    else:
        member = get_user_from_session(False)
        if member and member.authentication_method == AuthenticationMethods.WEBSITE and not WebsiteAuth.select(member_id=member.member_id)[0].verified:
            alert = "You haven't verified your email yet!"
            verification_data = awaiting_verification.get(member.member_id)
            if not verification_data or verification_data["expires"] - time.time() < (60 * 10) - (60 * 3):
                alert += """ Click <b><a href="#" onclick="apiRequest('send_verification_email'); new bootstrap.Alert('#alert').close();">here</a></b> to resend the verification email, or"""
            alert += " click <b><a href='/settings'>here</a></b> to go to the settings and change your email address."

    return render_template("index.html", alert=alert)

@app.route("/login")
def login_template():
    if "session_token" in session: return redirect("/")

    alert = session.get("alert")
    if alert: session.pop("alert")
    return render_template("login.html", alert=alert)

@app.route("/signup")
def signup_template():
    if "session_token" in session: return redirect("/")

    alert = session.get("alert")
    if alert: session.pop("alert")
    return render_template("signup.html", alert=alert)

@app.route("/play")
def play_template(): return render_template("play.html")

# endregion

# region assets

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static/assets"), "favicon.ico", mimetype="image/vnd.microsoft.icon")

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

    app.run("0.0.0.0", debug=True)