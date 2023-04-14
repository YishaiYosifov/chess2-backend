import os

from flask import Blueprint, send_from_directory

assets = Blueprint("assets", __name__)

@assets.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(os.path.dirname(assets.root_path), "static/assets"), "favicon.ico", mimetype="image/vnd.microsoft.icon")

@assets.route("/static/uploads/<member_id>/profile-picture.jpeg")
def profile_picture(member_id : str):
    """
    Get a user's profile picture. If the user hasn't uploaded a picture yet, return the default one
    """

    root_path = os.path.dirname(assets.root_path)
    if os.path.exists(f"static/uploads/{member_id}/profile-picture.jpeg"): return send_from_directory(os.path.join(root_path, f"static/uploads/{member_id}"), "profile-picture.jpeg", mimetype="image/jpeg")
    else: return send_from_directory(os.path.join(root_path, "static/assets"), "default-profile-picture.jpg", mimetype="image/jpg")