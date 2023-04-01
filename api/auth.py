from werkzeug.exceptions import HTTPException, BadRequest, Conflict, Unauthorized, NotFound, InternalServerError

from flask_restful.reqparse import Argument
from flask import Blueprint, redirect

import bcrypt

from dao.auth import *
from util import *

auth = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth.route("/signup", methods=["POST"])
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

    hash = bcrypt.hashpw(password, bcrypt.gensalt())

    auth = WebsiteAuth(member_id=member_id, hash=hash)
    auth.insert()

    send_verification_email(email, auth)
    os.makedirs(f"static/uploads/{member_id}")

    session["alert"] = "Signed Up Successfully"
    return "Signed Up", 200

@auth.route("/login", methods=["POST"])
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
    if not bcrypt.checkpw(password, auth.hash): raise Unauthorized("Unknown email / username / password")

    member.session_token = uuid.uuid4().hex
    member.update()
    session["session_token"] = member.session_token

    return "Logged In", 200

@auth.route("/logout", methods=["POST", "GET"])
@requires_authentication(type=Member)
def logout(user : Member):
    session.clear()
    user.session_token = ""
    user.update()
    return redirect("/")