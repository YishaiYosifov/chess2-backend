from werkzeug.exceptions import HTTPException, BadRequest, Conflict, Unauthorized, NotFound, InternalServerError

from flask_restful.reqparse import Argument
from flask import Blueprint, redirect

from dao.auth import *
from util import *

profile = Blueprint("profile", __name__, url_prefix="/api/profile/<username>")

@profile.route("/get_info", methods=["POST", "GET"])
def get_user_info(username : str):
    if username == "me":
        user : Member = get_user_from_session()
        return user.get_private_info()
    
    user : Member = Member.select(username=username)
    if not user: raise NotFound("User Not Found")
    user = user[0]
    
    return user.get_public_info(), 200
