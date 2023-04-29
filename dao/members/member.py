from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

import uuid
import os

from werkzeug.exceptions import BadRequest, Conflict, TooManyRequests
from flask import request, session

import requests

from .auth import AuthMethods, WebsiteAuth
from .session_token import SessionToken
from .rating import Rating

from extensions import CONFIG, EMAIL_REG, COUNTRIES
from app import db

PUBLIC_INFO = ["member_id", "username", "about", "country", "country_alpha"]
PRIVATE_INFO = ["email", "auth_method", "username_last_changed"]

class Member(db.Model):
    __tablename__ = "members"

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

    member_id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Text)

    username = db.Column(db.String(30))
    email = db.Column(db.String(256))

    country = db.Column(db.String(100), default="International")
    country_alpha = db.Column(db.String(5), default="INTR")

    about = db.Column(db.Text)
    last_color = db.Column(db.String(10), default="white")

    auth_method = db.Column(db.Enum(AuthMethods))
    username_last_changed = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    rating = db.relationship("Rating", backref="member", uselist=False, cascade="all, delete-orphan")
    session_tokens = db.relationship("SessionToken", backref="member", cascade="all, delete-orphan")

    email_verification = db.relationship("EmailVerification", uselist=False, backref="member", cascade="all, delete-orphan")

    outgoing_game = db.relationship("OutgoingGame", backref="member", uselist=False, cascade="all, delete-orphan")

    def get_public_info(self) -> dict: return self._get(PUBLIC_INFO)
    def get_private_info(self) -> dict: return self.get_public_info() | self._get(PRIVATE_INFO)

    def _get(self, attributes : list) -> dict[str:any]:
        """
        Get attributes from the object

        :param attributes: the attribute to get
        """
        results = {}
        for attribute in attributes:
            value = getattr(self, attribute)
            if isinstance(value, Enum): value = value.value
            results[attribute] = value
        return results

    def delete(self):
        self.logout()

        if self.auth_method == AuthMethods.WEBSITE: WebsiteAuth.query.filter_by(member=self).delete()

        Rating.query.filter_by(member=self).delete()
        SessionToken.query.filter_by(member=self).delete()

        db.session.delete(self)
    
    def insert(self):
        """
        Create user
        """
        
        db.session.add(self)
        db.session.flush()

        if not os.path.exists(f"static/uploads/{self.member_id}"): os.makedirs(f"static/uploads/{self.member_id}")
        for mode in CONFIG["modes"]: db.session.add(Rating(member=self, mode=mode))

    def set_username(self, username : str):
        """
        Update the username

        :param username: the new username

        :raises BadRequest: the username is not valid (too long / too short / includes a space)
        :raises TooManyRequests: the username was changed recently
        :raises Conflict: the username is taken
        """

        now = datetime.now()
        if self.username_last_changed and self.username_last_changed < now - timedelta(weeks=4) > 0: raise TooManyRequests("Username Changed Recently")
        elif len(username) > 30: raise BadRequest("Username Too Long")
        elif len(username) < 1: raise BadRequest("Username Too Short")
        elif " " in username: raise BadRequest("Username can't include a space")
        elif Member.query.filter_by(username=username).first(): raise Conflict("Username Taken")

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
        elif Member.query.filter_by(email=email).first(): raise Conflict("Email Taken")

        self.email = email

        if send_verification:
            # Send the verification email

            auth : WebsiteAuth = WebsiteAuth.query.filter_by(member=self).first()
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
        db.session.add(SessionToken(member=self, token=token))
    
    def logout(self):
        SessionToken.query.filter_by(token=session["session_token"]).delete()
        session.clear()
    
    @classmethod
    def create_guest(cls):
        guest = cls(username=f"guest-{uuid.uuid4().hex[:8]}", auth_method=AuthMethods.GUEST)
        guest.insert()
        return guest