from typing import Callable
from enum import Enum

from flask import Blueprint, session, render_template, redirect
from pydantic import BaseModel

from .assets import assets

from dao import AuthMethods, User, active_games
from util import try_get_user_from_session

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

def change_password_helper(**kwargs):
    user = try_get_user_from_session()
    if user.auth_method != AuthMethods.WEBSITE: return redirect("/settings")

    return True

def user_helper(**kwargs):
    username = kwargs.get("username")
    if not username:
        user = try_get_user_from_session(False)
        if not user: return redirect("/")
        
        return redirect(f"/user/{user.username}")
    
    user : User = User.query.filter_by(username=username).first()
    if not user or user.auth_method == AuthMethods.GUEST: return redirect("/")

    return True

def game_helper(**kwargs):
    game_token = kwargs.get("game_token")
    if not game_token in active_games: return redirect("/")

    return True

@frontend.route("/")
def index():
    alert = session.get("alert")
    if alert: session.pop("alert")

    if try_get_user_from_session(must_logged_in=False): return render_template("index-authorized.html", alert=alert)
    else: return render_template("index-unauthorized.html", alert=alert)

TEMPLATES = [
    Template(route="/login", template="login.html", auth_req=AuthReq.NOT_AUTHED),
    Template(route="/signup", template="signup.html", auth_req=AuthReq.NOT_AUTHED),

    Template(route="/user/<username>", template="user.html", helper=user_helper),
    Template(route="/user", template="user.html", helper=user_helper),

    Template(route="/settings", template="settings.html", auth_req=AuthReq.REQUIRED),
    Template(route="/settings/password", template="change-password.html", auth_req=AuthReq.REQUIRED, helper=change_password_helper),

    Template(route="/play", template="play.html"),
    Template(route="/game/<game_token>", template="game.html", helper=game_helper)
]

def default_template(template : Template, **kwargs):
    if template.auth_req == AuthReq.REQUIRED: try_get_user_from_session()
    elif template.auth_req == AuthReq.NOT_AUTHED and try_get_user_from_session(must_logged_in=False): return redirect("/")

    if template.helper:
        helper_return = template.helper(**kwargs)
        if not helper_return is True: return helper_return
    
    alert = session.get("alert")
    if alert: session.pop("alert")

    return render_template(template.template, alert=alert)