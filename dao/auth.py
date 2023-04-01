from enum import Enum

from pydantic import BaseModel

from .database_model import DatabaseModel

class AuthenticationMethods(Enum):
    WEBSITE = "website"
    GMAIL = "gmail"
    GUEST = "guest"

class WebsiteAuth(BaseModel, DatabaseModel):
    _table = "website_authentication"

    website_auth_id : int = None
    member_id : int
    
    verified : bool = False

    hash : str