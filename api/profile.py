import numpy
import os
import io

from werkzeug.exceptions import NotFound, Unauthorized, Conflict, UnprocessableEntity, RequestEntityTooLarge

from flask_restful.reqparse import Argument
from flask import Blueprint, request

from PIL import Image

from dao.auth import *
from util import *

profile = Blueprint("profile", __name__, url_prefix="/profile/<target>")

@profile.route("/get_info", methods=["POST"])
def get_info(target : str):
    if target == "me":
        user : Member = get_user_from_session()
        return user.get_private_info()
    
    user : Member = Member.select(username=target)
    if not user: raise NotFound("User Not Found")
    user = user[0]
    
    return user.get_public_info(), 200

REQUIRES_PASSWORD = ["username", "email"]
@profile.route("/update", methods=["POST"])
@requires_arguments(Argument("username", type=str), Argument("email", type=str), Argument("about", type=str), Argument("password_confirmation", type=str, default=""))
@requires_authentication(type=Member)
def update(target : str, user : Member, args):
    if target != user.username and target != "me": raise Unauthorized("Not logged into target user")

    for item in REQUIRES_PASSWORD:
        if args.get(item):
            if not user.check_password(args.password_confirmation): raise Unauthorized("Wrong Password Confirmation")
            break

    if args.username != None: user.set_username(args.username)
    if args.email != None:
        if user.authentication_method != AuthenticationMethods.WEBSITE: raise Conflict("Can only update email when using website auth")

        user.set_email(args.email)
        auth : WebsiteAuth = WebsiteAuth.select(member_id=user.member_id)[0]
        auth.verified = False
        auth.update()

        send_verification_email(user.email, auth)
    if args.about != None: user.about = args.about

    user.update()
    return "Updated", 200

@profile.route("/upload_profile_picture", methods=["POST"])
@requires_authentication(type=Member)
def upload_profile_picture(target : str, user : Member):
    if target != user.username and target != "me": raise Unauthorized("Not logged into target user")

    data = request.files.get("profile-picture")
    if not data: raise BadRequest("Missing Profile Picture")

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

    width, height = image.size
    box_size = min(width, height)

    left = (width - box_size) / 2
    top = (height - box_size) / 2
    right = (width + box_size) / 2
    bottom = (height + box_size) / 2

    image = image.crop((left, top, right, bottom))
    image = image.resize((160, 160))
    image.save(f"static/uploads/{user.member_id}/profile-picture.jpeg")

    return "Uploaded", 200