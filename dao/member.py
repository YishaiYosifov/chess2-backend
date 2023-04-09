from __future__ import annotations

import time

from werkzeug.exceptions import BadRequest, Conflict, TooManyRequests
from pydantic import BaseModel

import bcrypt

from .auth import AuthenticationMethods, WebsiteAuth
from .database_model import DatabaseModel

PUBLIC_INFO = ["member_id", "username", "about"]
PRIVATE_INFO = ["email", "authentication_method", "username_last_changed"]

class Member(BaseModel, DatabaseModel):
    _table = "members"

    member_id : int = None
    session_token : str = None

    username : str = None
    email : str = None
    about : str = ""

    authentication_method : AuthenticationMethods
    username_last_changed : int = None

    def get_public_info(self) -> dict: return super().get(PUBLIC_INFO)
    def get_private_info(self) -> dict: return self.get_public_info() | super().get(PRIVATE_INFO)

    def set_username(self, username : str):
        if (self.username_last_changed + 60 * 60 * 24 * 30) - time.time() > 0: raise TooManyRequests("Username Changed Recently")
        elif len(username) > 60: raise BadRequest("Username Too Long")
        elif len(username) < 1: raise BadRequest("Username Too Short")
        elif Member.select(username=username): raise Conflict("Username Taken")

        self.username_last_changed = int(time.time())
        self.username = username

    def set_email(self, email : str):
        from util import EMAIL_REG

        email_match = EMAIL_REG.match(email)
        if not email_match or email_match.group(0) != email: raise BadRequest("Invalid Email Address")
        elif Member.select(email=email): raise Conflict("Email Taken")

        self.email = email
    
    def check_password(self, password : str) -> bool:
        if self.authentication_method != AuthenticationMethods.WEBSITE: raise AttributeError("Only Website Auth requires password")
        
        auth : WebsiteAuth = WebsiteAuth.select(member_id=self.member_id)[0]
        return bcrypt.checkpw(password, auth.hash)