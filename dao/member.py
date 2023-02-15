from __future__ import annotations

from pydantic import BaseModel

from .database_model import DatabaseModel
from .auth import AuthenticationMethods

class Member(BaseModel, DatabaseModel):
    _table = "members"

    member_id : int = None
    session_token : str = None

    username : str
    email : str

    authentication_method : AuthenticationMethods