import time

from flask import Blueprint, session, render_template, redirect

from .assets import assets

from dao.auth import *
from util import *

frontend = Blueprint("frontend", __name__, template_folder="templates")
frontend.register_blueprint(assets)

@frontend.route("/")
def index_template():
    alert = session.get("alert")
    if alert: session.pop("alert")

    return render_template("index.html", alert=alert)

@frontend.route("/login")
def login_template():
    if "session_token" in session: return redirect("/")

    alert = session.get("alert")
    if alert: session.pop("alert")
    return render_template("login.html", alert=alert)

@frontend.route("/signup")
def signup_template():
    if "session_token" in session: return redirect("/")

    alert = session.get("alert")
    if alert: session.pop("alert")
    return render_template("signup.html", alert=alert)

@frontend.route("/settings")
def settings_template():
    if not "session_token" in session: return redirect("/login")

    alert = session.get("alert")
    if alert: session.pop("alert")
    return render_template("settings.html", alert=alert)

@frontend.route("/play")
def play_template(): return render_template("play.html")