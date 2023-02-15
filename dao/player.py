import uuid

from .auth import AuthenticationMethods
from .member import Member

class Player(Member):
    sid : str = None

    @classmethod
    def create_guest(cls):
        return cls(token=uuid.uuid4().hex, session_token=uuid.uuid4().hex, username="guest-" + uuid.uuid4().hex[:8], authentication_method=AuthenticationMethods.GUEST)