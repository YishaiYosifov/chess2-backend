from typing import Annotated
from http import HTTPStatus

from argon2.exceptions import VerifyMismatchError
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Response, Header, Cookie
from argon2 import PasswordHasher

from app.schemas import user_schema


class OAuth2PasswordBearerCookie(OAuth2PasswordBearer):
    def _get_from_header(
        self, auth_header: str | None
    ) -> user_schema.AuthTokens:
        """Create a AuthTokens model with the Authorization header"""

        if auth_header:
            scheme, _, token = auth_header.partition(" ")
        else:
            scheme, token = "", ""

        return (
            user_schema.AuthTokens()
            if not auth_header or scheme.lower() != "bearer"
            else user_schema.AuthTokens(access_token=token, refresh_token=token)
        )

    def _is_auth_empty(self, schema: user_schema.AuthTokens) -> bool:
        return schema.access_token is None and schema.refresh_token is None

    def __call__(
        self,
        auth_header: Annotated[
            str | None,
            Header(alias="Authorization"),
        ] = None,
        access_token_cookie: Annotated[
            str | None,
            Cookie(alias="access_token"),
        ] = None,
        refresh_token_cookie: Annotated[
            str | None,
            Cookie(alias="refresh_token"),
        ] = None,
    ) -> user_schema.AuthTokens:
        """
        Handle authentication logic.
        This function first tries to get the token from the header, then the cookies.
        """

        if auth_header:
            tokens = self._get_from_header(auth_header)
        else:
            tokens = user_schema.AuthTokens(
                access_token=access_token_cookie,
                refresh_token=refresh_token_cookie,
            )

        if self._is_auth_empty(tokens) and self.auto_error:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return tokens


oauth2_scheme = OAuth2PasswordBearerCookie(
    tokenUrl="auth/login", auto_error=False
)

password_hasher = PasswordHasher()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def set_auth_cookies(
    response: Response,
    access_token: str | None = None,
    refresh_token: str | None = None,
    access_token_max_age: int = 15 * 60,
    refresh_token_max_age: int = 60 * 60 * 24 * 30,
) -> None:
    """
    Set authentication cookies in the response object

    :param response: the fastapi response object to set the cookies on
    :param access_token: the access token to be set as a cookie
    :param access_token_max_age: when should the access token cookie expire
    :param refresh_token: the refresh token to be set as a cookie
    :param refresh_token_max_age: when should the refresh token cookie expire
    """

    if access_token:
        response.set_cookie(
            "access_token",
            access_token,
            expires=access_token_max_age,
            max_age=access_token_max_age,
            httponly=True,
            secure=True,
        )

    if refresh_token:
        response.set_cookie(
            "refresh_token",
            refresh_token,
            expires=refresh_token_max_age,
            max_age=refresh_token_max_age,
            httponly=True,
            secure=True,
        )


def remove_auth_cookies(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
