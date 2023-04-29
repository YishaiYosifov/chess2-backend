from typing import Callable

import numpy
import os
import io

from werkzeug.exceptions import NotFound, Unauthorized, UnprocessableEntity, RequestEntityTooLarge, BadRequest

from flask import Blueprint, request, jsonify
from flask_restful.reqparse import Argument
from pydantic import BaseModel

from PIL import Image

from util import requires_args, requires_auth, try_get_user_from_session
from dao import Game, AuthMethods, User, WebsiteAuth
from app import db

profile = Blueprint("profile", __name__, url_prefix="/profile/<target>")

@profile.route("/get_info", methods=["POST"])
def get_info(target : str):
    """
    Get a user's information
    """

    if target == "me":
        # If the target is the logged in user, get the user from the session and return the private information
        user : User = try_get_user_from_session()
        return user.get_private_info()
    
    # Select the user using the given username
    user : User = User.query.filter_by(username=target).first()
    if not user: raise NotFound("User Not Found")
    
    # Return the public info
    return user.get_public_info(), 200

@profile.route("/get_games", methods=["POST"])
@requires_args(Argument("limit", type=int, default=10))
def get_games(target : str, args):
    """
    Get a user's played games
    """

    # Find the target user
    target : User = User.query.filter_by(username=target).first()
    if not target: raise NotFound("User Not Found")

    if args.limit > 100: raise BadRequest("Can only fetch up to 100 games")

    # Get a list of the games
    games : list[Game] = Game.query.filter((Game.is_over == True) & ((Game.white == target) | (Game.black == target))).limit(args.limit).all()
    games_data = []

    # Convert it to json
    for game in games:
        data = game.to_dict(exclude=["white", "black"])
        data["white"] = game.white.username if game.white else "DELETED"
        data["black"] = game.black.username if game.black else "DELETED"

        games_data.append(data)

    return jsonify(games_data), 200

class Setting(BaseModel):
    name : str
    type : type

    requires_password : bool = False
    set_value : Callable

SETTINGS = [
    Setting(name="username", type=str, set_value=lambda user, value: user.set_username(value)),
    Setting(name="email", type=str, requires_password=True, set_value=lambda user, _, value: user.set_email(value)),

    Setting(name="country", type=str, set_value=lambda user, value: user.set_country(value)),
    Setting(name="about", type=str, set_value=lambda user, value: setattr(user, "about", value)),

    Setting(name="password", type=str, requires_password=True, set_value=lambda _, auth, value: auth.set_password(value))
]
@profile.route("/update", methods=["POST"])
@requires_args(*([Argument(setting.name, type=setting.type) for setting in SETTINGS] + [Argument("password_confirmation", type=str, default="")]))
@requires_auth()
def update(target : str, user : User, args):
    """
    Update the user information
    """

    # If target is not the logged in user, raise an unauthorized exception
    if target != user.username and target != "me": raise Unauthorized("Not logged into target user")

    # Loop through every setting that doesn't require password confirmation and was given a new value and call the set function
    for setting in filter(lambda setting: not setting.requires_password and args[setting.name] != None, SETTINGS):
        setting.set_value(user, args[setting.name])

    if user.auth_method == AuthMethods.WEBSITE:
        # Get every setting that requries password confirmation and was given a new value
        requires_password = list(filter(lambda setting: setting.requires_password and args[setting.name] != None, SETTINGS))
        if requires_password:
            # If there are any, get the user's website auth and check the password
            auth : WebsiteAuth = WebsiteAuth.query.filter_by(user=user).first()
            if not auth.check_password(args.password_confirmation): raise Unauthorized("Wrong Password Confirmation")

            # Set the new value
            for setting in requires_password: setting.set_value(user, auth, args[setting.name])

    db.session.commit()
    return "Updated", 200

@profile.route("/upload_profile_picture", methods=["POST"])
@requires_auth()
def upload_profile_picture(target : str, user : User):
    """
    Upload a new profile picture
    """

    # If target is not the logged in user, raise an unauthorized exception
    if target != user.username and target != "me": raise Unauthorized("Not logged into target user")

    # Get the picture from the request
    data = request.files.get("profile-picture")
    if not data: raise BadRequest("Missing Profile Picture")

    # Get the file size
    file_size = data.seek(0, os.SEEK_END)
    data.seek(0, os.SEEK_SET)
    
    # If the file is larger than 2mb, raise a RequestEntityTooLarge exception
    if file_size > 1.049e+6: raise RequestEntityTooLarge("Profile Picture too big")
    # If the file doesn't have a png, jpeg or jpg extension, raise an UnprocessableEntity exception
    if not data.filename.split(".")[-1] in ["png", "jpeg", "jpg"]: raise UnprocessableEntity("Profile picture must be png/jpeg/jpg")

    # Read the file
    blob = data.read()
    buffer = io.BytesIO(blob)
    buffer.seek(0)
    
    # Convert it into a pillow object, than into a numpy array and back to a pillow object to remove any potential malware
    image = Image.open(buffer)
    image = numpy.asarray(image)
    image = Image.fromarray(image).convert("RGB")

    # Centre crop the image
    width, height = image.size
    box_size = min(width, height)

    left = (width - box_size) / 2
    top = (height - box_size) / 2
    right = (width + box_size) / 2
    bottom = (height + box_size) / 2

    image = image.crop((left, top, right, bottom))
    image = image.resize((160, 160))

    # Save it
    image.save(f"static/uploads/{user.user_id}/profile-picture.jpeg")

    return "Uploaded", 200