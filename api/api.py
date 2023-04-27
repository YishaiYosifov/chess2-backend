from flask import Blueprint, redirect, session, request
from werkzeug.exceptions import Conflict

from .profile import profile
from .auth import auth
from .game import game

from dao import WebsiteAuth, Member, EmailVerification, PoolConn
from util import requires_auth, send_verification_email

api = Blueprint("api", __name__, url_prefix="/api")
api.register_blueprint(auth)
api.register_blueprint(profile)
api.register_blueprint(game)

@api.route("/verify_email/<token>", methods=["GET"])
def verify_email(user_id, token):
    """
    This function will run when a user clicks verify in the email
    """

    try: user_id = int(user_id)
    except ValueError: user_id = 0
    
    # Check if the email verification id is correct
    verification_data : EmailVerification = EmailVerification.select(token=token).first()
    if not verification_data or verification_data.token != token:
        session["alert"] = {"message": "Verification Link Expired", "color": "danger"}
        return redirect("/")

    # Get the user auth and set verified to true
    auth : WebsiteAuth = WebsiteAuth.select(member_id=verification_data.member_id)
    auth.verified = True
    auth.update()

    verification_data.delete()

    session["alert"] = {"message": "Email Verified!", "color": "success"}
    return redirect("/")

@api.route("/send_verification_email", methods=["POST"])
@requires_auth()
def send_verification_email_route(user : Member):
    """
    Send a verification email
    """

    auth : WebsiteAuth = WebsiteAuth.select(member_id=user.member_id).first()
    if auth.verified: raise Conflict("Already Verified")

    send_verification_email(user.email, auth)
    return "Email Sent", 200