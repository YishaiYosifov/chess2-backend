import numpy
import os
import io

from werkzeug.exceptions import NotFound, Unauthorized, UnprocessableEntity, RequestEntityTooLarge

from flask_restful.reqparse import Argument
from flask import Blueprint, request

from PIL import Image

from dao.auth import *
from util import *

profile = Blueprint("profile", __name__, url_prefix="/profile/<target>")

@profile.route("/get_info", methods=["POST"])
def get_info(target : str):
    """
    Get a user's information
    """

    if target == "me":
        # If the target is the logged in user, get the user from the session and return the private information
        user : Member = get_user_from_session()
        return user.get_private_info()
    
    # Select the user using the given username
    user : Member = Member.select(username=target)
    if not user: raise NotFound("User Not Found")
    user = user[0]
    
    # Return the public info
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
    """
    Update the user information
    """

    # If target is not the logged in user, raise an unauthorized exception
    if target != user.username and target != "me": raise Unauthorized("Not logged into target user")

    # Loop through every setting that doesn't require password confirmation and was given a new value and call the set function
    for setting, data in filter(lambda setting: not setting[1]["requires_password"] and args[setting[0]] != None, SETTINGS.items()):
        data["set"](user, args[setting])

    if user.authentication_method == AuthenticationMethods.WEBSITE:
        # Get every setting that requries password confirmation and was given a new value
        requires_password = dict(filter(lambda setting: setting[1]["requires_password"] and args[setting[0]] != None, SETTINGS.items()))
        if requires_password:
            # If there are any, get the user's website auth and check the password
            auth = user.get_website_auth()
            if not auth.check_password(args.password_confirmation): raise Unauthorized("Wrong Password Confirmation")

            # Set the new value
            for setting, data in requires_password.items(): data["set"](user, auth, args[setting])
            auth.update()

    user.update()
    return "Updated", 200

@profile.route("/upload_profile_picture", methods=["POST"])
@requires_authentication(type=Member)
def upload_profile_picture(target : str, user : Member):
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
    image.save(f"static/uploads/{user.member_id}/profile-picture.jpeg")

    return "Uploaded", 200