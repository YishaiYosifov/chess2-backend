from __future__ import annotations

from datetime import datetime, timedelta

import uuid
import os

from werkzeug.exceptions import BadRequest, Conflict, TooManyRequests
from flask import request, session

import requests

from .auth import AuthMethods, WebsiteAuth
from .rating_archive import RatingArchive
from ..games import Game

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

    last_accessed = db.Column(db.DateTime, server_default=db.text("(UTC_TIMESTAMP)"))
    created_at = db.Column(db.DateTime, server_default=db.text("(UTC_TIMESTAMP)"))

    # Relationships
    email_verification = db.relationship("EmailVerification", uselist=False, backref="user", cascade="all, delete-orphan")

    outgoing_game = db.relationship("OutgoingGames", backref="inviter", foreign_keys="OutgoingGames.inviter_id", uselist=False, cascade="all, delete-orphan")
    incoming_games = db.relationship("OutgoingGames", backref="recipient", foreign_keys="OutgoingGames.recipient_id", cascade="all, delete-orphan")

    def __eq__(self, to):
        from ..games.player import Player
        if not isinstance(to, User) and not isinstance(to, Player): return False
        return to.user_id == self.user_id or (self.player_in and to == self.player_in)
    
    @property
    def active_game(self) -> Game:
        if not self._active_game: self._active_game = Game.query.filter((Game.is_over == db.false()) & (Game.white.has(user=self) | Game.black.has(user=self))).first()
        return self._active_game
    _active_game = None
    
    def get_public_info(self) -> dict:
        from util import column_to_dict
        return column_to_dict(self, include=PUBLIC_INFO)
    def get_private_info(self) -> dict:
        from util import column_to_dict
        return self.get_public_info() | column_to_dict(self, include=PRIVATE_INFO)

    def rating(self, mode : str):
        rating_archive = RatingArchive.query.filter_by(user=self, mode=mode).order_by(RatingArchive.rating_id.desc()).first()
        if not rating_archive:
            rating_archive = RatingArchive(user=self, mode=mode)
            db.session.add(rating_archive)
        return rating_archive

    def delete(self):
        if self.auth_method == AuthMethods.WEBSITE: WebsiteAuth.query.filter_by(user=self).delete()
        RatingArchive.query.filter_by(user=self).delete()
        try: session.clear()
        except RuntimeError: pass

        db.session.delete(self)
    
    def insert(self):
        """
        Create user
        """
        
        db.session.add(self)
        db.session.flush()

        if self.auth_method != AuthMethods.GUEST and not os.path.exists(f"static/uploads/{self.user_id}"): os.makedirs(f"static/uploads/{self.user_id}")
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
        elif all(char.isdigit() for char in username): raise BadRequest("Username can't be just numbers")
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
    
    @classmethod
    def create_guest(cls):
        print("Created Guest")
        guest = cls(username=f"guest-{uuid.uuid4().hex[:8]}", auth_method=AuthMethods.GUEST)
        guest.insert()

        session["user_id"] = guest.user_id
        return guest