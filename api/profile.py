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

@profile.route("/update", methods=["POST"])
@requires_arguments(Argument("username", type=str), Argument("email", type=str))
@requires_authentication(type=Member)
def update(target : str, user : Member, args):
    if target != user.username and target != "me": raise Unauthorized("Not logged into target user")

    if args.username != None: user.set_username(args.username)
    if args.email != None:
        if user.authentication_method != AuthenticationMethods.WEBSITE: raise Conflict("Can only update email when using website auth")

        user.set_email(args.email)
        auth : WebsiteAuth = WebsiteAuth.select(member_id=user.member_id)[0]
        auth.verified = False
        auth.update()

        send_verification_email(user.email, auth)
    if "profile_picture" in request.files:
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
        image.save(f"static/uploads/{user.member_id}/profile-picture.jpeg")

    user.update()
    return "Updated", 200