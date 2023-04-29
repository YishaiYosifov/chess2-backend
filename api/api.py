from flask import Blueprint, redirect, session
from werkzeug.exceptions import Conflict

from .profile import profile
from .auth import auth
from .game import game

from util import requires_auth, send_verification_email
from dao import WebsiteAuth, User, EmailVerification
from app import db

api = Blueprint("api", __name__, url_prefix="/api")
api.register_blueprint(auth)
api.register_blueprint(profile)
api.register_blueprint(game)

@api.route("/verify_email/<token>", methods=["GET"])
def verify_email(token):
    """
    This function will run when a user clicks verify in the email
    """
    
    # Check if the email verification id is correct
    verification_data : EmailVerification = EmailVerification.query.filter_by(token=token).first()
    if not verification_data or verification_data.token != token:
        session["alert"] = {"message": "Verification Link Expired", "color": "danger"}
        return redirect("/")

    # Get the user auth and set verified to true
    WebsiteAuth.query.filter_by(user=verification_data.user).verified = True
    db.session.delete(verification_data)
    db.session.commit()

    session["alert"] = {"message": "Email Verified!", "color": "success"}
    return redirect("/")

@api.route("/send_verification_email", methods=["POST"])
@requires_auth()
def send_verification_email_route(user : User):
    """
    Send a verification email
    """

    auth : WebsiteAuth = WebsiteAuth.query.filter_by(user_id=user.user_id).first()
    if auth.verified: raise Conflict("Already Verified")

    send_verification_email(user.email, auth)
    return "Email Sent", 200