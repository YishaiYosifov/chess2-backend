from datetime import timedelta, datetime
from typing import Any
from http import HTTPStatus
import uuid
import time

from starlette.requests import Request
from fastapi.security import utils as fastapi_security_utils
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, Response
from jose import jwt, JWTError

from app.models.jti_blocklist_model import JTIBlocklist
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


# region encode jwt


def _encode_jwt_token(
    secret_key: str,
    jwt_algorithm: str,
    data: dict[str, Any],
    expires_in_delta: timedelta,
):
    """
    Encode a jwt token with specified data.
    This function automatically sets exp, iat and nbf

    :param secret_key: the secret key to sign the token with
    :param jwt_algorithm: which algorithm to use to generate the key
    :param data: the data to encode
    :param expires_in_delta: time until the token expires
    """

    expire = datetime.utcnow() + expires_in_delta
    timestamp = int(time.time())
    to_encode = {
        "exp": expire,
        "iat": timestamp,
        "nbf": timestamp,
    }
    to_encode.update(data)

    encoded_jwt = jwt.encode(
        to_encode,
        secret_key,
        algorithm=jwt_algorithm,
    )
    return encoded_jwt


def create_access_token(
    secret_key: str,
    jwt_algorithm: str,
    user_id: int,
    expires_in_minutes: int = 30,
    fresh: bool = False,
) -> str:
    """
    Generate a JWT access token

    :param secret_key: the secret key to sign the token with
    :param jwt_algorithm: which algorithm to use to generate the key
    :param user_id: the user id to incode in the token
    :param expires_in_minutes: when should this token expires
    :return: the encoded jwt access token
    """

    return _encode_jwt_token(
        secret_key,
        jwt_algorithm,
        {"sub": str(user_id), "type": "access", "fresh": fresh},
        timedelta(minutes=expires_in_minutes),
    )


def create_refresh_token(
    secret_key: str,
    jwt_algorithm: str,
    user_id: int,
    expires_in_days: int = 30,
) -> str:
    """
    Generate a JWT refresh token

    :param secret_key: the secret key to sign the token with
    :param jwt_algorithm: which algorithm to use to generate the key
    :param user_id: the user id to incode in the token
    :param expires_in_days: when should this token expires
    :return: the encoded jwt refresh token
    """

    return _encode_jwt_token(
        secret_key,
        jwt_algorithm,
        {
            "sub": str(user_id),
            "type": "refresh",
            "jti": str(uuid.uuid4()),
        },
        timedelta(days=expires_in_days),
    )


# endregion


# region decode jwt


def _decode_jwt_token(
    secret_key: str,
    jwt_algorithm: str,
    token: str,
    options: dict[str, bool] = {},
) -> dict[str, Any]:
    """
    Decode a jwt token

    :param secret_key: the secret key to sign the token with
    :param jwt_algorithm: which algorithm to use to generate the key
    :param options: options to update the default decode options
    :return: a dictionary containing the jwt payload
    """

    options = {
        "require_exp": True,
        "require_iat": True,
        "require_nbf": True,
    } | options

    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[jwt_algorithm],
            options=options,
        )
        return payload
    except JWTError:
        return {}


def _get_jwt_indentity(payload: dict[str, Any]) -> int | None:
    """
    Try to get the user id from a jwt token.

    :param payload: the decoded payload returned from the jwt token
    :return: the user_id if it was found, otherwise None
    """

    user_id: str | None = payload.get("sub")
    return int(user_id) if user_id and user_id.isnumeric() else None


def decode_access_token(
    secret_key: str, jwt_algorithm: str, token: str, fresh: bool = False
) -> int | None:
    """
    Try to decode an access token into a user id

    :param secret_key: the secret key to sign the token with
    :param jwt_algorithm: which algorithm to use to generate the key
    :param token: the jwt token
    :return: the user id if decoding was successful, otherwise None
    """

    payload = _decode_jwt_token(secret_key, jwt_algorithm, token)
    if payload.get("type") != "access" or (not payload.get("fresh") and fresh):
        return

    return _get_jwt_indentity(payload)


def _check_token_revocation(db: Session, payload: dict[str, Any]) -> bool:
    """
    Check if the token jti is blocklisted

    :param db: an sqlalchemy session to check for revocation in
    :param payload: the decoded payload returned from the jwt token
    :return: whether the token is revoked
    """

    return (
        db.execute(
            select(JTIBlocklist).filter_by(jti=payload.get("jti"))
        ).scalar()
        is not None
    )


def decode_refresh_token(
    secret_key: str,
    jwt_algorithm: str,
    db: Session,
    token: str,
) -> int | None:
    """
    Try to decode a refresh token into a user id

    :param secret_key: the secret key to sign the token with
    :param jwt_algorithm: which algorithm to use to generate the key
    :param db: a db session to search for expired jtis in
    :param token: the jwt token
    :return: the user id if decoding was successful, otherwise None
    """

    payload = _decode_jwt_token(
        secret_key, jwt_algorithm, token, {"require_jti": True}
    )
    if payload.get("type") != "refresh" or _check_token_revocation(db, payload):
        return

    return _get_jwt_indentity(payload)


# endregion


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
