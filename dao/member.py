from __future__ import annotations

import uuid

from pydantic import BaseModel
from enum import Enum

class AuthenticationMethods(Enum):
    WEBSITE = "website"
    GMAIL = "gmail"
    GUEST = "guest"

class Member(BaseModel):
    member_id : int
    session_token : str

    username : str
    email : str

    authentication_method : AuthenticationMethods

    def insert(self):
        from util import database, cursor

        params = self.to_dict()
        cursor.execute(f"INSERT INTO members ({', '.join(params.keys())}) VALUES ({', '.join(['%s'] * len(params))})", list(params.values()))
        database.commit()
    
    def update(self):
        from util import database, cursor

        params = self.to_dict()
        cursor.execute(f"UPDATE members SET {', '.join([param + '=%s' for param in params.keys()])} WHERE member_id=%s", list(params.values()) + [self.member_id])
        database.commit()
    
    @classmethod
    def select(cls, **params) -> list[Member]:
        from util import cursor

        cursor.execute(f"SELECT * FROM members WHERE {' '.join([param + '=%s' for param in params.keys()])}", list(params.values()))
        return [cls.parse_obj(member) for member in cursor.fetchall()]
    
    def to_dict(self) -> dict[str:any]:
        variables = {}
        for key, value in self.__dict__.items():
            if key == "member_id" or key.startswith("__") or callable(key): continue

            if isinstance(value, Enum): value = value.value
            variables[key] = value
        
        return variables

class WebsiteAuth(BaseModel):
    website_auth_id : int
    hash : str
    salt : str

class Player(Member):
    sid : str = None

    @classmethod
    def create_guest(cls):
        return cls(token=uuid.uuid4().hex, session_token=uuid.uuid4().hex, username="guest-" + uuid.uuid4().hex[:8], authentication_method=AuthenticationMethods.GUEST)