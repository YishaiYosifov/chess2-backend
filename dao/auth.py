from enum import Enum

from werkzeug.exceptions import BadRequest
from pydantic import BaseModel

import bcrypt

from .database_model import DatabaseModel

class AuthenticationMethods(Enum):
    WEBSITE = "website"
    GMAIL = "gmail"
    GUEST = "guest"

class WebsiteAuth(BaseModel, DatabaseModel):
    _table = "website_authentication"

    website_auth_id : int = None
    member_id : int = None
    
    verified : bool = False

    hash : str = None

    def set_password(self, password : str):
        from util import STRONG_PASSWORD_REG

        if not STRONG_PASSWORD_REG.findall(password): raise BadRequest("Invalid Password")
        hash = bcrypt.hashpw(password, bcrypt.gensalt())
        self.hash = hash

    def check_password(self, password : str) -> bool: return bcrypt.checkpw(password, self.hash)