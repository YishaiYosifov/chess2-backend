from enum import Enum

from werkzeug.exceptions import BadRequest

import bcrypt

from ..database_model import DatabaseModel

class AuthMethods(Enum):
    WEBSITE = "website"
    GMAIL = "gmail"
    GUEST = "guest"

class WebsiteAuth(DatabaseModel):
    __tablename__ = "website_auth"
    __primary__ = "website_auth_id"

    website_auth_id : int = None
    member_id : int = None
    
    verified : bool = False

    hash : str = None

    def set_password(self, password : str):
        """
        Update the password

        :param password: the new password

        :raises BadRequest: the password doesn't match the password requirements
        """

        from extensions import STRONG_PASSWORD_REG

        if not STRONG_PASSWORD_REG.findall(password): raise BadRequest("Invalid Password")
        hash = bcrypt.hashpw(password, bcrypt.gensalt())
        self.hash = hash

    def check_password(self, password : str) -> bool: return bcrypt.checkpw(password.encode(), self.hash.encode())