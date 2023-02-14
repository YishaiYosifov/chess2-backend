from pydantic import BaseModel

import uuid

class Member(BaseModel):
    token : str
    session_token : str

    username : str

class Player(Member):
    sid : str = None
    is_guest : bool = False

    @classmethod
    def create_guest(cls):
        return cls(token=uuid.uuid4().hex, session_token=uuid.uuid4().hex, username="guest-" + uuid.uuid4().hex[:8], is_guest=True)