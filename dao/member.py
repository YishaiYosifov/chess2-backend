from __future__ import annotations

from pydantic import BaseModel

from .database_model import DatabaseModel
from .auth import AuthenticationMethods

PUBLIC_INFO = ["username"]

class Member(BaseModel, DatabaseModel):
    _table = "members"

    member_id : int = None
    session_token : str = None

    username : str
    email : str

    authentication_method : AuthenticationMethods

    def get_public_info(self) -> dict: return {param: self.__dict__[param] for param in PUBLIC_INFO}