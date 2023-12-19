from http import HTTPStatus

from starlette.requests import Request
from fastapi.security import utils as fastapi_security_utils
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from fastapi import HTTPException, Response

from app.schemas import user_schema


class OAuth2PasswordBearerCookie(OAuth2PasswordBearer):
    def _get_from_header(self, request: Request) -> user_schema.AuthTokens:
        """Create a AuthTokens model with the Authorization header"""

        auth_header = request.headers.get("Authorization")
        scheme, token = fastapi_security_utils.get_authorization_scheme_param(
            auth_header
        )

        return (
            user_schema.AuthTokens()
            if not auth_header or scheme.lower() != "bearer"
            else user_schema.AuthTokens(access_token=token, refresh_token=token)
        )

    def _get_from_cookie(self, request: Request) -> user_schema.AuthTokens:
        """Create a AuthTokens models with the access and refresh token cookies"""

        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")
        return user_schema.AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def _is_auth_empty(self, schema: user_schema.AuthTokens) -> bool:
        return schema.access_token is None and schema.refresh_token is None

    def __call__(self, request: Request) -> user_schema.AuthTokens:
        """
        Handle authentication logic.
        This function first tries to get the token from the header, then the cookies.
        """

        header_tokens = self._get_from_header(request)
        cookie_tokens = self._get_from_cookie(request)
        tokens = (
            cookie_tokens
            if self._is_auth_empty(header_tokens)
            else header_tokens
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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


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
            max_age=access_token_max_age,
            httponly=True,
            secure=True,
        )

    if refresh_token:
        response.set_cookie(
            "refresh_token",
            refresh_token,
            max_age=refresh_token_max_age,
            httponly=True,
            secure=True,
        )


def remove_auth_cookies(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
