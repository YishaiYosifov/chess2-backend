from werkzeug.exceptions import BadRequest, Unauthorized

from flask import Blueprint, redirect, jsonify
from flask_restful.reqparse import Argument

import shutil

from dao import WebsiteAuth, AuthenticationMethods
from util import *

auth = Blueprint("auth", __name__, url_prefix="/auth")

@auth.route("/signup", methods=["POST"])
@requires_arguments(Argument("username", type=str, required=True), Argument("password", type=str, required=True), Argument("email", type=str, required=True))
def signup(args):
    """
    Create a new account
    """

    # Get the account information
    username = args.username
    password = args.password
    email = args.email
    
    # Create a member object and add all the information
    member = Member(authentication_method=AuthenticationMethods.WEBSITE)
    member.set_username(username)
    member.set_email(email, False)

    # Create a website auth object and add the password
    auth = WebsiteAuth()
    auth.set_password(password)

    # Insert the user into the database
    member.insert()
    
    # Get the auto increment member_id and add it to the website auth
    member_id = cursor.lastrowid
    auth.member_id = member_id

    # Insert the website auth into the database
    auth.insert()

    # Send the verification email
    send_verification_email(email, auth)

    session["alert"] = {"message": "Signed Up Successfully", "color": "success"}
    return "Signed Up", 200

@auth.route("/login", methods=["POST"])
@requires_arguments(Argument("selector", type=str, required=True), Argument("password", type=str, required=True))
def login(args):
    """
    Login to a user
    """

    # Get the selector (email / username) and password
    selector = args.selector
    password = args.password

    # Select the user using the assuming the selector is the username, if it doesn't find the user select assuming the selector is the email address
    member : Member = Member.select(username=selector)
    if not member:
        member : Member = Member.select(email=selector)
        if not member: raise Unauthorized("Unknown email / username / password")
    member = member[0]
    
    if member.authentication_method != AuthenticationMethods.WEBSITE: raise BadRequest("Wrong Authorization Method")

    # Check the password
    auth = member.get_website_auth()
    if not auth.check_password(password): raise Unauthorized("Unknown email / username / password")

    # Generate the session token
    member.gen_session_token()

    return "Logged In", 200

@auth.route("/is_logged_in", methods=["POST"])
def is_logged_in(): return jsonify("session_token" in session), 200

@auth.route("/logout", methods=["POST", "GET"])
@requires_authentication(type=Member)
def logout(user : Member):
    """
    Logout a user
    """

    user.logout()
    return redirect("/")

@auth.route("/delete", methods=["POST"])
@requires_authentication(type=Member)
def delete(user : Member):
    """
    Delete a user's account
    """
    
    shutil.rmtree(f"static/uploads/{user.member_id}")

    user.delete()
    
    return "Deleted", 200