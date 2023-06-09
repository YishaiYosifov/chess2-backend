from typing import Callable
from enum import Enum

from flask import Blueprint, session, render_template, redirect
from pydantic import BaseModel

from .assets import assets

from util import try_get_user_from_session
from dao import AuthMethods, User, Game
from app import db

frontend = Blueprint("frontend", __name__, template_folder="templates")
frontend.register_blueprint(assets)

class AuthReq(Enum):
    OPTIONAL = 0
    REQUIRED = 1
    NOT_AUTHED = 2

class Template(BaseModel):
    route : str
    template : str

    auth_req : AuthReq = AuthReq.OPTIONAL

    helper : Callable = None

# region helpers

def change_password_helper():
    user = try_get_user_from_session()
    if user.auth_method != AuthMethods.WEBSITE: return redirect("/settings")

    return True

def user_helper(**kwargs):
    username = kwargs.get("username")
    if not username:
        user = try_get_user_from_session(force_logged_in=False)
        if not user: return redirect("/")
        
        return redirect(f"/user/{user.username}")
    
    user : User = User.query.filter_by(username=username).first()
    if not user or user.auth_method == AuthMethods.GUEST: return redirect("/")

    return True

def game_helper(**kwargs):
    game_token = kwargs.get("game_token")
    game = Game.query.filter_by(token=game_token).first()
    if not game: return redirect("/play")
    elif not game.is_over:
        user = try_get_user_from_session(force_logged_in=False, allow_guests=True)
        if not user or (user != game.white and user != game.black): return redirect("/play")

    return True

def play_helper():
    user = try_get_user_from_session(allow_guests=True)
    if user.active_game: return redirect(f"/game/{user.active_game.token}")
    return True

# endregion

TEMPLATES = [
    Template(route="/", template="index.html"),
    
    Template(route="/login", template="login.html", auth_req=AuthReq.NOT_AUTHED),
    Template(route="/signup", template="signup.html", auth_req=AuthReq.NOT_AUTHED),
    Template(route="/logout", template="logout.html", auth_req=AuthReq.REQUIRED),

    Template(route="/user/<username>", template="user.html", helper=user_helper),
    Template(route="/user", template="user.html", helper=user_helper),

    Template(route="/settings", template="settings.html", auth_req=AuthReq.REQUIRED),
    Template(route="/settings/password", template="change-password.html", auth_req=AuthReq.REQUIRED, helper=change_password_helper),

    Template(route="/play", template="play.html", helper=play_helper),
    Template(route="/game/<game_token>", template="game.html", helper=game_helper)
]

def default_template(template : Template, **kwargs):
    if template.auth_req == AuthReq.REQUIRED: try_get_user_from_session()
    elif template.auth_req == AuthReq.NOT_AUTHED and try_get_user_from_session(force_logged_in=False): return redirect("/")

    if template.helper:
        helper_return = template.helper(**kwargs)
        if not helper_return is True: return helper_return
    
    alert = session.get("alert")
    if alert: session.pop("alert")

    return render_template(template.template, alert=alert)