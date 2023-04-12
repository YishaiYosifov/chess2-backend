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


SETTINGS = {
    "about": {
        "requires_password": False,
        "set": lambda user, about: setattr(user, "about", about)
    },
    "username": {
        "requires_password": False,
        "set": lambda user, username: user.set_username(username)
    },
    "email": {
        "requires_password": True,
        "set": lambda user, _, email: user.set_email(email)
    },
    "password": {
        "requires_password": True,
        "set": lambda _, auth, password: auth.set_password(password)
    }
}
@profile.route("/update", methods=["POST"])
@requires_arguments(Argument("username", type=str), Argument("email", type=str), Argument("password", type=str), Argument("about", type=str), Argument("password_confirmation", type=str, default=""))
@requires_authentication(type=Member)
def update(target : str, user : Member, args):
    if target != user.username and target != "me": raise Unauthorized("Not logged into target user")

    for setting, data in filter(lambda setting: not setting[1]["requires_password"] and args[setting[0]] != None, SETTINGS.items()):
        data["set"](user, args[setting])

    if user.authentication_method == AuthenticationMethods.WEBSITE:
        requires_password = list(filter(lambda setting: setting[1]["requires_password"] and args[setting[0]] != None, SETTINGS.items()))
        if requires_password:
            auth = user.get_website_auth()
            if not auth.check_password(args.password_confirmation): raise Unauthorized("Wrong Password Confirmation")

            for setting, data in requires_password: data["set"](user, auth, args[setting])
            auth.update()

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