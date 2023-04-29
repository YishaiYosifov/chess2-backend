from typing import Callable
from enum import Enum

from flask import Blueprint, session, render_template, redirect
from pydantic import BaseModel

from .assets import assets

from util import try_get_user_from_session
from dao import AuthMethods, User

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

    return {"context": {}}

def user_helper(**kwargs):
    username = kwargs.get("username")
    if not username:
        user = try_get_user_from_session(False)
        if not user: return redirect("/")
        
        return redirect(f"/user/{user.username}")
    elif not User.query.filter_by(username=username).first(): return redirect("/")

    return {"context": {}}

def index_helper(**kwargs):
    alert = session.get("alert")
    if alert: session.pop("alert")

    if try_get_user_from_session(must_logged_in=False): return render_template("index-authorized.html", alert=alert)
    else: return render_template("index-unauthorized.html", alert=alert)

TEMPLATES = [
    Template(route="/", template="index.html", helper=index_helper),

    Template(route="/login", template="login.html", auth_req=AuthReq.NOT_AUTHED),
    Template(route="/signup", template="signup.html", auth_req=AuthReq.NOT_AUTHED),

    Template(route="/user/<username>", template="user.html", helper=user_helper),
    Template(route="/user", template="user.html", helper=user_helper),

    Template(route="/settings", template="settings.html", auth_req=AuthReq.REQUIRED),
    Template(route="/settings/password", template="change-password.html", auth_req=AuthReq.REQUIRED, helper=change_password_helper),

    Template(route="/play", template="play.html")
]

def default_template(template : Template, **kwargs):
    if template.auth_req == AuthReq.REQUIRED: try_get_user_from_session()
    elif template.auth_req == AuthReq.NOT_AUTHED and try_get_user_from_session(must_logged_in=False): return redirect("/")
    
    context = {}
    if template.helper:
        helper_return = template.helper(**kwargs)
        if not isinstance(helper_return, dict): return helper_return
        context = helper_return["context"]
    
    alert = session.get("alert")
    if alert: session.pop("alert")

    return render_template(template.template, alert=alert, **context)