from pydantic import BaseModel

import uuid

from ..members.rating import Rating
from ..members.member import Member

class Player(BaseModel):
    def __init__(self, mode : str, **data):
        super().__init__(**data)

        if self.member: self.rating = Rating.select(member_id=self.member.member_id, mode=mode).first()
        else: self.rating = Rating()

    member : Member = None

    username : str = None
    rating : Rating = None

    is_guest : bool = False

    @classmethod
    def create_guest(cls): return cls(username="guest-" + uuid.uuid4().hex[:8], is_guest=True)