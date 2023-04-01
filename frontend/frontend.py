import time

from flask import Blueprint, session, render_template, redirect

from .assets import assets

from dao.auth import *
from util import *

frontend = Blueprint("frontend", __name__, "/")
frontend.register_blueprint(assets)

@frontend.route("/")
def index_template():
    alert = session.get("alert")
    if alert: session.pop("alert")
    else:
        member = get_user_from_session(False)
        if member and member.authentication_method == AuthenticationMethods.WEBSITE and not WebsiteAuth.select(member_id=member.member_id)[0].verified:
            alert = "You haven't verified your email yet!"
            verification_data = awaiting_verification.get(member.member_id)
            if not verification_data or verification_data["expires"] - time.time() < (60 * 10) - (60 * 3):
                alert += """ Click <b><a href="#" onclick="apiRequest('/send_verification_email'); new bootstrap.Alert('#alert').close();">here</a></b> to resend the verification email, or"""
            alert += " click <b><a href='/settings'>here</a></b> to go to the settings and change your email address."

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

@frontend.route("/play")
def play_template(): return render_template("play.html")