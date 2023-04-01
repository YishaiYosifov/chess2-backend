import numpy
import os
import io

from werkzeug.exceptions import Conflict, UnprocessableEntity, RequestEntityTooLarge

from flask import Blueprint, redirect
from PIL import Image

from .profile import profile
from .auth import auth

from dao.auth import *
from util import *

api = Blueprint("api", __name__, url_prefix="/api")
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

@api.route("/test", methods=["POST"])
def test():
    data = request.files["profile_picture"]
    file_size = data.seek(0, os.SEEK_END)
    data.seek(0, os.SEEK_SET)
    
    if file_size > 1.049e+6: raise RequestEntityTooLarge("Profile Picture too big")
    if not data.filename.split(".")[-1] in ["png", "jpeg", "jpg"]: raise UnprocessableEntity("Profile picture must be png/jpeg/jpg")

    blob = data.read()
    buffer = io.BytesIO(blob)
    buffer.seek(0)
    
    image = Image.open(buffer)
    image = numpy.asarray(image)
    image = Image.fromarray(image).convert("RGB")

    image = image.resize((160, 160))
    image.save("static/uploads/test.jpeg")
    return "pog", 200