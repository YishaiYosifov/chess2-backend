from datetime import datetime
from typing import Annotated

from pydantic import field_validator, BaseModel, EmailStr, Field

from app.types import CountryAlpha3


class UserIn(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=30)]
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def check_spaces(cls, value: str) -> str:
        if " " in value:
            raise ValueError("Cannot include spaces")
        return value

    @field_validator("username")
    @classmethod
    def check_not_just_numbers(cls, value: str) -> str:
        if all(char.isdigit() for char in value):
            raise ValueError("Cannot be just numbers")
        return value

    @field_validator("password")
    @classmethod
    def check_strong_password(cls, password: str) -> str:
        # Not the best but I don't care anymore
        if (
            len(password) < 8
            or not any(c.isupper() for c in password)
            or not any(c.islower() for c in password)
            or not any(c.isdigit() for c in password)
        ):
            raise ValueError(
                "Must be at least 8 characters long, have at least 1 upper"
                "and lower case letters and have a number"
            )
        return password


class PublicUserOut(BaseModel):
    user_id: int
    username: str
    first_name: str = ""
    last_name: str = ""
    about: str
    country_alpha3: CountryAlpha3 = "INT"
    location: str = ""
    pfp_last_changed: datetime


class PrivateUserOut(PublicUserOut):
    email: EmailStr
    username_last_changed: datetime | None


class EditableProfile(BaseModel):
    first_name: Annotated[str, Field(max_length=50)]
    last_name: Annotated[str, Field(max_length=50)]
    country_alpha3: CountryAlpha3
    location: Annotated[str, Field(max_length=40)]
    about: Annotated[str, Field(max_length=300)]


class AccessToken(BaseModel):
    token_type: str = "bearer"
    access_token: str | None = None


class AuthTokens(AccessToken):
    refresh_token: str | None = None
