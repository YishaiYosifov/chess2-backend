from enum import Enum

from werkzeug.exceptions import BadRequest

import bcrypt

from extensions import STRONG_PASSWORD_REG
from app import db

class AuthMethods(Enum):
    WEBSITE = "website"
    GMAIL = "gmail"
    GUEST = "guest"

class WebsiteAuth(db.Model):
    __tablename__ = "website_auths"

    website_auth_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    user = db.relationship("User", uselist=False)
    
    verified = db.Column(db.Boolean, default=False)
    hash = db.Column(db.Text)

    def set_password(self, password : str):
        """
        Update the password

        :param password: the new password

        :raises BadRequest: the password doesn't match the password requirements
        """

        if not STRONG_PASSWORD_REG.findall(password): raise BadRequest("Invalid Password")
        hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.hash = hash

    def check_password(self, password : str) -> bool: return bcrypt.checkpw(password.encode(), self.hash.encode())