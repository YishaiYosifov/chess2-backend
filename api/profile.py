from datetime import datetime
from typing import Callable

import numpy
import os
import io

from werkzeug.exceptions import NotFound, Unauthorized, UnprocessableEntity, RequestEntityTooLarge, BadRequest

from flask import Blueprint, request, jsonify
from flask_restful.reqparse import Argument
from pydantic import BaseModel

from PIL import Image

from util import requires_args, requires_auth, try_get_user_from_session, column_to_dict
from dao import Game, AuthMethods, User, WebsiteAuth, RatingArchive
from app import db

profile = Blueprint("profile", __name__, url_prefix="/profile/<target>")

@profile.route("/get_info", methods=["POST"])
@requires_args(Argument("include", type=str, action="append"))
def get_info(target : str, args):
    """
    Get a user's information
    """

    if target == "me":
        # If the target is the logged in user, get the user from the session and return the private information
        user : User = try_get_user_from_session(allow_guests=True)
        data = user.get_private_info()
    else:
        # Select the user using the given username
        user : User = User.query.filter_by(username=target).first() or User.query.filter_by(user_id=target).first()
        if not user: raise NotFound("User Not Found")
        data = user.get_public_info()
    
    if args.include: data = {name:value for name, value in data.items() if name in args.include}
    
    # Return the data
    return jsonify(data), 200

@profile.route("/get_games", methods=["POST"])
@requires_args(Argument("limit", type=int, default=10))
def get_games(target : str, args):
    """
    Get a user's played games
    """

    # Find the target user
    user : User = User.query.filter_by(username=target).first() or User.query.filter_by(user_id=target).first()
    if not user: raise NotFound("User Not Found")

    if args.limit > 100: raise BadRequest("Can only fetch up to 100 games")

    # Get a list of the games
    games : list[Game] = Game.query.filter((Game.is_over == db.true()) & (Game.white.has(user=user) | Game.black.has(user=user))).limit(args.limit).all()
    games_data = []

    # Convert it to json
    for game in games:
        games_data.append({
            "white": game.white.user.username if game.white else "DELETED",
            "black": game.black.user.username if game.black else "DELETED",
            "game_settings": column_to_dict(game.game_settings, exclude=["game_settings_id"]),
            "white_score": game.white.score,
            "black_score": game.black.score,
            "token": game.token
        })

    return jsonify(games_data), 200

@profile.route("/get_ratings", methods=["POST"])
@requires_args(Argument("mode", type=str, required=True), Argument("since", type=int))
def get_ratings(target : str, args):
    """
    Get rating information for a certain user
    """

    # Find the target user
    user : User = User.query.filter_by(username=target).first() or User.query.filter_by(user_id=target).first()
    if not user: raise NotFound("User Not Found")
    if not args.since: return jsonify(user.rating(args.mode).elo), 200

    since = datetime.utcfromtimestamp(args.since)

    filter_by = (RatingArchive.user == user) & (RatingArchive.achieved_at >= since)
    if args.mode != "all": filter_by &= (RatingArchive.mode == args.mode)
    ratings : list[RatingArchive] = RatingArchive.query.filter(filter_by).order_by(RatingArchive.achieved_at).all()

    formatted = {}
    for rating in ratings:
        if not rating.mode in formatted:
            max_rating = db.session.query(db.func.max(RatingArchive.elo)).filter(filter_by & (RatingArchive.mode == rating.mode)).scalar()
            min_rating = db.session.query(db.func.min(RatingArchive.elo)).filter(filter_by & (RatingArchive.mode == rating.mode)).scalar()
            formatted[rating.mode] = {"max": max_rating, "min": min_rating, "archive": []}

        formatted[rating.mode]["archive"].append(column_to_dict(rating))

    return jsonify(formatted), 200

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