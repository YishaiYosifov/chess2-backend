from __future__ import annotations

from pydantic import BaseModel

from .database_model import DatabaseModel
from .auth import AuthenticationMethods

PUBLIC_INFO = ["member_id", "username"]
PRIVATE_INFO = ["email"]

class Member(BaseModel, DatabaseModel):
    _table = "members"

    member_id : int = None
    session_token : str = None

    username : str
    email : str

    authentication_method : AuthenticationMethods

    def get_public_info(self) -> dict: return super().get(PUBLIC_INFO)
    def get_private_info(self) -> dict: return self.get_public_info() | super().get(PRIVATE_INFO)