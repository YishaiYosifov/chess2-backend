from werkzeug.exceptions import HTTPException, BadRequest, Conflict, Unauthorized, NotFound, InternalServerError

from flask_restful.reqparse import Argument
from flask import Blueprint, redirect

from .profile import profile
from .auth import auth

from dao.auth import *
from util import *

api = Blueprint("api", __name__, "/api")
api.register_blueprint(auth)
api.register_blueprint(profile)


@api.route("/verify_email/<user_id>/<id>", methods=["GET"])
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

@api.route("/send_verification_email", methods=["POST"])
@requires_authentication(type=Member)
def send_verification_email_route(user : Member):
    auth : WebsiteAuth = WebsiteAuth.select(member_id=user.member_id)[0]
    if auth.verified: raise Conflict("Already Verified")

    send_verification_email(user.email, auth)
    return "Email Sent", 200