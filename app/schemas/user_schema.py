from datetime import datetime
from typing import Annotated

from pydantic_extra_types.country import CountryAlpha3
from pydantic import field_validator, BaseModel, EmailStr, Field

from app.constants import constants


class BaseUserProfile(BaseModel):
    country: CountryAlpha3 | None = None
    about: Annotated[str, Field(max_length=300)] = ""


class BaseUserAccountInfo(BaseModel):
    username: Annotated[str, Field(max_length=30)]

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

    @field_validator("username")
    @classmethod
    def check_not_me(cls, value: str) -> str:
        if value == "me":
            raise ValueError("Cannot be 'me'")
        return value


class UserAccountInfoSensitive(BaseUserAccountInfo):
    email: EmailStr


class UserIn(UserAccountInfoSensitive):
    # password: str = Field(pattern=STRONG_PASSWORD_REGEX) - this will only work from pydantic 2.5
    password: str

    @field_validator("password")
    @classmethod
    def check_strong_password(cls, value: str) -> str:
        if not constants.STRONG_PASSWORD_REGEX.match(value):
            raise ValueError(
                "Must be at least 8 characters long, have at least 1 upper and lower case letters and have a number"
            )
        return value


class UserOut(BaseUserProfile, BaseUserAccountInfo):
    user_id: int
    pfp_last_changed: Annotated[datetime, Field(default_factory=datetime.now)]


class UserOutSensitive(UserOut, UserAccountInfoSensitive):
    pass
