import io
import os

from flask import Blueprint, send_from_directory, send_file
from werkzeug.exceptions import NotFound

from PIL import Image

from extensions import COUNTRIES

assets = Blueprint("assets", __name__)

@assets.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(os.path.dirname(assets.root_path), "static/assets"), "favicon.ico", mimetype="image/vnd.microsoft.icon")

FLAG_WIDTH = 46
FLAG_HEIGHT = 27
@assets.route("/assets/country/<country_code>")
def country(country_code):
    if not country_code in COUNTRIES: raise NotFound

    flags = Image.open("static/assets/flags.png")
    index = list(COUNTRIES.keys()).index(country_code)

    from_x = index * FLAG_WIDTH
    to_x = from_x + FLAG_WIDTH

    flag = flags.crop((
        from_x, 0,
        to_x, FLAG_HEIGHT
    ))

    buffer = io.BytesIO()
    flag.save(buffer, "png")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/jpeg")

@assets.route("/static/uploads/<user_id>/profile-picture.jpeg")
def profile_picture(user_id : str):
    """
    Get a user's profile picture. If the user hasn't uploaded a picture yet, return the default one
    """

    root_path = os.path.dirname(assets.root_path)
    if os.path.exists(f"static/uploads/{user_id}/profile-picture.jpeg"): return send_from_directory(os.path.join(root_path, f"static/uploads/{user_id}"), "profile-picture.jpeg", mimetype="image/jpeg")
    else: return send_from_directory(os.path.join(root_path, "static/assets"), "default-profile-picture.jpg", mimetype="image/jpg")