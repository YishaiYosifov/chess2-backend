from __future__ import annotations
from typing import Literal

import uuid
import time
import os

from werkzeug.exceptions import BadRequest, Conflict, TooManyRequests
from flask import request, session

import requests

from .auth import AuthMethods, WebsiteAuth
from .session_token import SessionToken
from .rating import Rating

from ..database_model import DatabaseModel

PUBLIC_INFO = ["member_id", "username", "about", "country", "country_alpha"]
PRIVATE_INFO = ["email", "auth_method", "username_last_changed"]

awaiting_verification : dict[str:dict["expires": str, "auth": WebsiteAuth]] = {}

class Member(DatabaseModel):
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

    __tablename__ = "members"
    __primary__ = "member_id"

    member_id : int = None
    sid : str = None

    username : str = None
    email : str = None

    country : str = "International"
    country_alpha : str = "INTR"

    about : str = ""
    last_color : Literal["white"] | Literal["black"] = "white"

    auth_method : AuthMethods
    username_last_changed : int = None

    def get_public_info(self) -> dict: return super().get(PUBLIC_INFO)
    def get_private_info(self) -> dict: return self.get_public_info() | super().get(PRIVATE_INFO)
    def get_website_auth(self) -> WebsiteAuth:
        """
        Get the website auth
        
        :raises Conflict: the user is not a website auth user
        """
        if self.auth_method != AuthMethods.WEBSITE: raise Conflict("Not Website Auth")

        return WebsiteAuth.select(member_id=self.member_id).first()

    def delete(self):
        super().delete()
        self.logout()

        try:
            auth = self.get_website_auth()
            auth.delete()
        except Conflict: pass

        Rating.delete_all(member_id=self.member_id)
        SessionToken.delete_all(member_id=self.member_id)
    
    def insert(self):
        """
        Create user
        """
        
        super().insert()

        from extensions import CONFIG

        if not os.path.exists(f"static/uploads/{self.member_id}"): os.makedirs(f"static/uploads/{self.member_id}")
        for mode in CONFIG["modes"]: Rating(member_id=self.member_id, mode=mode).insert()

    def set_username(self, username : str):
        """
        Update the username

        :param username: the new username

        :raises BadRequest: the username is not valid (too long / too short / includes a space)
        :raises TooManyRequests: the username was changed recently
        :raises Conflict: the username is taken
        """

        if self.username_last_changed and (self.username_last_changed + 60 * 60 * 24 * 30) - time.time() > 0: raise TooManyRequests("Username Changed Recently")
        elif len(username) > 30: raise BadRequest("Username Too Long")
        elif len(username) < 1: raise BadRequest("Username Too Short")
        elif " " in username: raise BadRequest("Username can't include a space")
        elif Member.select(username=username).first(): raise Conflict("Username Taken")

        self.username_last_changed = int(time.time())
        self.username = username

    def set_email(self, email : str, send_verification = True):
        """
        Update the email address

        :param email: the new email
        :param send_verification: whether to send a new verification email

        :raises BadRequest: the email is not valid
        :raises Conflict: the email address is taken
        """

        from util import send_verification_email
        from extensions import EMAIL_REG

        # Get the website auth
        auth = self.get_website_auth()

        # Check if the email address is valid and not taken
        email_match = EMAIL_REG.match(email)
        if not email_match or email_match.group(0) != email: raise BadRequest("Invalid Email Address")
        elif Member.select(email=email).first(): raise Conflict("Email Taken")

        self.email = email

        if send_verification:
            # Send the verification email
            send_verification_email(email, auth)
            auth.verified = False
    
    def set_country(self, alpha):
        """
        Update the country

        :param alpha: the alpha 2 of the country

        :raises BadRequest: invalid country
        """

        from extensions import COUNTRIES

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
        SessionToken(member_id=self.member_id, token=token).insert()
    
    def logout(self):
        token : SessionToken = SessionToken.select(token=session["session_token"]).first()
        if token: token.delete()

        session.clear()
    
    @classmethod
    def create_guest(cls):
        guest = cls(username=f"guest-{uuid.uuid4().hex[:8]}", auth_method=AuthMethods.GUEST)
        guest.insert()
        return guest