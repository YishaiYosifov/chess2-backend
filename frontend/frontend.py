from typing import Callable

from flask import Blueprint, session, render_template, redirect
from pydantic import BaseModel

from .assets import assets

from dao.auth import *
from util import *

frontend = Blueprint("frontend", __name__, template_folder="templates")
frontend.register_blueprint(assets)

class Template(BaseModel):
    route : str
    template : str

    requires_auth : bool = False
    requires_unauth : bool = False

    special_function : Callable = None

def change_password_template_special():    
    member = get_user_from_session(False)
    if member.authentication_method != AuthenticationMethods.WEBSITE: return redirect("/settings")

    return True

TEMPLATES = [
    Template(route="/", template="index.html"),

    Template(route="/login", template="login.html", requires_unauth=True),
    Template(route="/signup", template="signup.html", requires_unauth=True),

    Template(route="/settings", template="settings.html", requires_auth=True),
    Template(route="/settings/password", template="change-password.html", requires_auth=True, special_function=change_password_template_special),

    Template(route="/play", template="play.html")
]

def default_template(template : Template):
    print(template)

    logged_in = "session_token" in session
    if (template.requires_auth and not logged_in) or \
        (template.requires_unauth and logged_in): return redirect("/")
    
    if template.special_function:
        special_return = template.special_function()
        if not special_return is True: return special_return
    
    alert = session.get("alert")
    if alert: session.pop("alert")
    return render_template(template.template, alert=alert)