from __future__ import annotations

from datetime import datetime, timedelta

import uuid
import os

from werkzeug.exceptions import BadRequest, Conflict, TooManyRequests
from flask import request, session

import requests

from .auth import AuthMethods, WebsiteAuth
from .rating_archive import RatingArchive
from .session_token import SessionToken

from extensions import CONFIG, EMAIL_REG, COUNTRIES
from app import db

PUBLIC_INFO = ["user_id", "username", "about", "country", "country_alpha"]
PRIVATE_INFO = ["email", "auth_method", "username_last_changed"]

class User(db.Model):
    __tablename__ = "users"

    def __init__(self, **data):
        try:
            ip = request.headers.getlist("X-Forwarded-For")
            if ip:
                response = requests.get(f"http://ip-api.com/json/{ip[0]}", params={"fields": "status,message,country,countryCode"})
                if response.status_code == 200:
                    ipinfo = response.json()
                    if ipinfo["status"] == "success":
                        data["country"] = ipinfo["country"]
                        data["country_alpha"] = ipinfo["countryCode"]
        except: pass
        
        super().__init__(**data)

    user_id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Text)

    username = db.Column(db.String(30))
    email = db.Column(db.String(256))

    country = db.Column(db.String(100), server_default="International")
    country_alpha = db.Column(db.String(5), server_default="INTR")

    about = db.Column(db.Text)
    last_color = db.Column(db.String(10), server_default="white")

    auth_method = db.Column(db.Enum(AuthMethods))
    username_last_changed = db.Column(db.DateTime, server_default=db.text("(UTC_TIMESTAMP)"))

    # Relationships
    session_tokens = db.relationship("SessionToken", backref="user", cascade="all, delete-orphan")

    email_verification = db.relationship("EmailVerification", uselist=False, backref="user", cascade="all, delete-orphan")

    outgoing_game = db.relationship("OutgoingGames", backref="inviter", foreign_keys="OutgoingGames.inviter_id", uselist=False, cascade="all, delete-orphan")
    incoming_games = db.relationship("OutgoingGames", backref="recipient", foreign_keys="OutgoingGames.recipient_id", cascade="all, delete-orphan")

    def get_public_info(self) -> dict:
        from util import get_from_column
        return get_from_column(self, PUBLIC_INFO)
    def get_private_info(self) -> dict:
        from util import get_from_column
        return self.get_public_info() | get_from_column(self, PRIVATE_INFO)

    def rating(self, mode : str): return RatingArchive.query.filter_by(user=self, mode=mode).order_by(RatingArchive.rating_id.desc()).first()

    def delete(self):
        self.logout()

        if self.auth_method == AuthMethods.WEBSITE: WebsiteAuth.query.filter_by(user=self).delete()

        RatingArchive.query.filter_by(user=self).delete()
        SessionToken.query.filter_by(user=self).delete()

        db.session.delete(self)
    
    def insert(self):
        """
        Create user
        """
        
        db.session.add(self)
        db.session.flush()

        if not os.path.exists(f"static/uploads/{self.user_id}"): os.makedirs(f"static/uploads/{self.user_id}")
        for mode in CONFIG["MODES"]: db.session.add(RatingArchive(user=self, mode=mode))

    def set_username(self, username : str):
        """
        Update the username

        :param username: the new username

        :raises BadRequest: the username is not valid (too long / too short / includes a space)
        :raises TooManyRequests: the username was changed recently
        :raises Conflict: the username is taken
        """

        now = datetime.utcnow()
        if self.username_last_changed and self.username_last_changed < now - timedelta(weeks=4) > 0: raise TooManyRequests("Username Changed Recently")
        elif len(username) > 30: raise BadRequest("Username Too Long")
        elif len(username) < 1: raise BadRequest("Username Too Short")
        elif " " in username: raise BadRequest("Username can't include a space")
        elif User.query.filter_by(username=username).first(): raise Conflict("Username Taken")

        self.username_last_changed = now
        self.username = username

    def set_email(self, email : str, send_verification = True):
        """
        Update the email address

        :param email: the new email
        :param send_verification: whether to send a new verification email

        :raises BadRequest: the email is not valid
        :raises Conflict: the email address is taken
        :raises Conflict: not website auth
        """

        from util import send_verification_email

        if self.auth_method != AuthMethods.WEBSITE: raise Conflict("Not Website Auth")

        # Check if the email address is valid and not taken
        email_match = EMAIL_REG.match(email)
        if not email_match or email_match.group(0) != email: raise BadRequest("Invalid Email Address")
        elif User.query.filter_by(email=email).first(): raise Conflict("Email Taken")

        self.email = email

        if send_verification:
            # Send the verification email

            auth : WebsiteAuth = WebsiteAuth.query.filter_by(user=self).first()
            send_verification_email(email, auth)
            auth.verified = False
    
    def set_country(self, alpha):
        """
        Update the country

        :param alpha: the alpha 2 of the country

        :raises BadRequest: invalid country
        """

        country = COUNTRIES.get(alpha)
        if not country: raise BadRequest("Invalid Country")

        self.country = country
        self.country_alpha = alpha
    
    def gen_session_token(self):
        """
        Generate a new session token
        """

        token = uuid.uuid4().hex
        session["session_token"] = token
        db.session.add(SessionToken(user=self, token=token))
    
    def logout(self):
        SessionToken.query.filter_by(token=session["session_token"]).delete()
        session.clear()
    
    @classmethod
    def create_guest(cls):
        guest = cls(username=f"guest-{uuid.uuid4().hex[:8]}", auth_method=AuthMethods.GUEST)
        guest.insert()
        return guest