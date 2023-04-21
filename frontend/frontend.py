from typing import Callable
from enum import Enum

from flask import Blueprint, session, render_template, redirect
from pydantic import BaseModel

from .assets import assets

from dao.auth import *
from util import *

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
    member = get_user_from_session()
    if member.authentication_method != AuthenticationMethods.WEBSITE: return redirect("/settings")

    return {"context": {}}

def member_helper(**kwargs):
    username = kwargs.get("username")
    if not username:
        member = get_user_from_session(False)
        if not member: return redirect("/")

        return redirect(f"/member/{member.username}")
    elif not Member.select(username=username): return redirect("/")

    return {"context": {}}

def index_helper(**kwargs):
    alert = session.get("alert")
    if alert: session.pop("alert")

    if "session_token" in session: return render_template("index-authorized.html", alert=alert)
    else: return render_template("index-unauthorized.html", alert=alert)

TEMPLATES = [
    Template(route="/", template="index.html", helper=index_helper),

    Template(route="/login", template="login.html", auth_req=AuthReq.NOT_AUTHED),
    Template(route="/signup", template="signup.html", auth_req=AuthReq.NOT_AUTHED),

    Template(route="/member/<username>", template="member.html", helper=member_helper),
    Template(route="/member", template="member.html", helper=member_helper),

    Template(route="/settings", template="settings.html", auth_req=AuthReq.REQUIRED),
    Template(route="/settings/password", template="change-password.html", auth_req=AuthReq.REQUIRED, helper=change_password_helper),

    Template(route="/play", template="play.html")
]

def default_template(template : Template, **kwargs):
    logged_in = "session_token" in session
    if (template.auth_req == AuthReq.REQUIRED and not logged_in) or \
        (template.auth_req == AuthReq.NOT_AUTHED and logged_in): return redirect("/")
    
    context = {}
    if template.helper:
        helper_return = template.helper(**kwargs)
        if not isinstance(helper_return, dict): return helper_return
        context = helper_return["context"]
    
    alert = session.get("alert")
    if alert: session.pop("alert")

    return render_template(template.template, alert=alert, **context)