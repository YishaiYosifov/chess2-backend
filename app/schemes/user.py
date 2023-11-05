from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class BaseUser(BaseModel):
    username: str
    about: str
    country: str


class UserIn(BaseUser):
    password: str
    email: EmailStr


class UserOut(BaseUser):
    user_id: int
    pfp_last_changed: datetime = Field(default_factory=datetime.now)
