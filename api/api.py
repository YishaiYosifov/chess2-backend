from werkzeug.exceptions import Conflict

from flask import Blueprint, redirect

from .profile import profile
from .auth import auth

from dao.auth import *
from util import *

api = Blueprint("api", __name__, url_prefix="/api")
api.register_blueprint(auth)
api.register_blueprint(profile)

@api.route("/verify_email/<user_id>/<id>", methods=["GET"])
def verify_email(user_id, id):
    try: user_id = int(user_id)
    except ValueError: user_id = 0
    
    verification_data = awaiting_verification.get(user_id)
    if not verification_data or verification_data["id"] != id:
        session["alert"] = {"message": "Verification Link Expired", "color": "danger"}
        return redirect("/")

    auth : WebsiteAuth = verification_data["auth"]
    auth.verified = True
    auth.update()

    awaiting_verification.pop(user_id)

    session["alert"] = {"message": "Email Verified!", "color": "success"}
    return redirect("/")

@api.route("/send_verification_email", methods=["POST"])
@requires_authentication(type=Member)
def send_verification_email_route(user : Member):
    auth : WebsiteAuth = WebsiteAuth.select(member_id=user.member_id)[0]
    if auth.verified: raise Conflict("Already Verified")

    send_verification_email(user.email, auth)
    return "Email Sent", 200