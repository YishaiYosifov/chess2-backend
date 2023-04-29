from werkzeug.exceptions import BadRequest, Unauthorized

from flask import Blueprint, redirect, jsonify, session
from flask_restful.reqparse import Argument

import shutil

from util import send_verification_email, requires_args, requires_auth, try_get_user_from_session
from dao import WebsiteAuth, AuthMethods, User
from app import db

auth = Blueprint("auth", __name__, url_prefix="/auth")

@auth.route("/signup", methods=["POST"])
@requires_args(Argument("username", type=str, required=True), Argument("password", type=str, required=True), Argument("email", type=str, required=True))
def signup(args):
    """
    Create a new account
    """

    # Get the account information
    username = args.username
    password = args.password
    email = args.email
    
    # Create a user object and add all the information
    user = User(auth_method=AuthMethods.WEBSITE)
    user.set_username(username)
    user.set_email(email, False)

    # Insert the user into the database
    user.insert()
    db.session.commit()

    # Create a website auth object and add the password
    auth = WebsiteAuth(user=user)
    auth.set_password(password)

    # Insert the website auth into the database
    db.session.add(auth)
    db.session.commit()

    # Send the verification email
    send_verification_email(email, auth)

    session["alert"] = {"message": "Signed Up Successfully", "color": "success"}
    return "Signed Up", 200

@auth.route("/login", methods=["POST"])
@requires_args(Argument("selector", type=str, required=True), Argument("password", type=str, required=True))
def login(args):
    """
    Login to a user
    """

    # Get the selector (email / username) and password
    selector = args.selector
    password = args.password

    # Select the user using the assuming the selector is the username, if it doesn't find the user select assuming the selector is the email address
    user : User = User.query.filter_by(username=selector).first()
    if not user:
        user : User = User.query.filter_by(email=selector).first()
        if not user: raise Unauthorized("Unknown email / username / password")
    
    if user.auth_method != AuthMethods.WEBSITE: raise BadRequest("Wrong Authorization Method")

    # Check the password
    auth : WebsiteAuth = WebsiteAuth.query.filter_by(user=user).first()
    if not auth.check_password(password): raise Unauthorized("Unknown email / username / password")

    # Generate the session token
    user.gen_session_token()
    db.session.commit()

    return "Logged In", 200

@auth.route("/is_logged_in", methods=["POST"])
def is_logged_in(): return jsonify(bool(try_get_user_from_session(must_logged_in=False, raise_on_session_expired=False))), 200

@auth.route("/logout", methods=["POST", "GET"])
@requires_auth()
def logout(user : User):
    """
    Logout a user
    """

    user.logout()
    return redirect("/")

@auth.route("/delete", methods=["POST"])
@requires_auth()
def delete(user : User):
    """
    Delete a user's account
    """
    
    user.delete()
    db.session.commit()
    shutil.rmtree(f"static/uploads/{user.user_id}")
    
    return "Deleted", 200