from .camel_model import CamelModel


class ConflictError(CamelModel):
    details: dict[str, str]


class UnauthorizedError(CamelModel):
    details: str


class AccessToken(CamelModel):
    access_token: str


class RefreshToken(AccessToken):
    refresh_token: str
