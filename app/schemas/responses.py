from typing import TypeVar, Generic

from pydantic import BaseModel

E = TypeVar("E", dict, str, list)


class ResponseError(BaseModel, Generic[E]):
    details: E


class AccessToken(BaseModel):
    token_type: str = "bearer"
    access_token: str


class AuthTokens(AccessToken):
    refresh_token: str
