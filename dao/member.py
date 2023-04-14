from __future__ import annotations

import time

from werkzeug.exceptions import BadRequest, Conflict, TooManyRequests
from pydantic import BaseModel

from .auth import AuthenticationMethods, WebsiteAuth
from .database_model import DatabaseModel

PUBLIC_INFO = ["member_id", "username", "about"]
PRIVATE_INFO = ["email", "authentication_method", "username_last_changed"]

class Member(BaseModel, DatabaseModel):
    _table = "members"
    _primary = "member_id"

    member_id : int = None
    session_token : str = None

    username : str = None
    email : str = None
    about : str = ""

    authentication_method : AuthenticationMethods
    username_last_changed : int = None

    def get_public_info(self) -> dict: return super().get(PUBLIC_INFO)
    def get_private_info(self) -> dict: return self.get_public_info() | super().get(PRIVATE_INFO)
    def get_website_auth(self) -> WebsiteAuth:
        """
        Get the website auth
        
        :raises Conflict: the user is not a website auth user
        """
        if self.authentication_method != AuthenticationMethods.WEBSITE: raise Conflict("Not Website Auth")

        auth = WebsiteAuth.select(member_id=self.member_id)
        return auth[0] if auth else None

    def delete(self):
        super().delete()

        auth = self.get_website_auth()
        if auth: auth.delete()

    def set_username(self, username : str):
        """
        Update the username

        :param username: the new username

        :raises BadRequest: the username is not valid (too long / too short)
        :raises TooManyRequests: the username was changed recently
        :raises Conflict: the username is taken
        """

        if self.username_last_changed and (self.username_last_changed + 60 * 60 * 24 * 30) - time.time() > 0: raise TooManyRequests("Username Changed Recently")
        elif len(username) > 60: raise BadRequest("Username Too Long")
        elif len(username) < 1: raise BadRequest("Username Too Short")
        elif Member.select(username=username): raise Conflict("Username Taken")

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

        from util import EMAIL_REG, send_verification_email

        # Get the website auth
        auth = self.get_website_auth()

        # Check if the email address is valid and not taken
        email_match = EMAIL_REG.match(email)
        if not email_match or email_match.group(0) != email: raise BadRequest("Invalid Email Address")
        elif Member.select(email=email): raise Conflict("Email Taken")

        self.email = email

        if send_verification:
            # Send the verification email
            send_verification_email(email, auth)
            auth.verified = False