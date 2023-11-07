from datetime import timedelta, datetime
from typing import Any
import uuid
import time

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.schemas.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def encode_jwt_token(data: dict, expires_in_delta: timedelta):
    """
    Encode a jwt token with specified data.
    This function automatically sets exp, iat and nbf

    :param data: the data to encode
    :param expires_in_delta: time until the token expires
    """

    to_encode: dict = data.copy()
    expire = datetime.utcnow() + expires_in_delta

    timestamp = int(time.time())
    to_encode.update(
        {
            "exp": expire,
            "iat": timestamp,
            "nbf": timestamp,
        }
    )

    settings = get_settings()
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def create_access_token(
    user_id: int,
    expires_in_minutes: int = 30,
) -> str:
    """
    Generate a JWT access token

    :param user_id: the user id to incode in the token
    :param expires_in_minutes: when should this token expires
    :return: the encoded jwt access token
    """

    return encode_jwt_token(
        {"sub": user_id, "type": "access"},
        timedelta(minutes=expires_in_minutes),
    )


def create_refresh_token(
    user_id: int,
    expires_in_days: int = 30,
) -> str:
    """
    Generate a JWT refresh token

    :param user_id: the user id to incode in the token
    :param expires_in_days: when should this token expires
    :return: the encoded jwt refresh token
    """

    return encode_jwt_token(
        {
            "sub": user_id,
            "type": "refresh",
            "jti": str(uuid.uuid4()),
        },
        timedelta(days=expires_in_days),
    )


def decode_access_token(token: str) -> int | None:
    """
    Try to get the user id from a jwt token.

    :param token: the jwt token itself
    :return: the user_id if the decode was successful, otherwise None
    """

    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id: Any | None = payload.get("sub")
        return user_id if isinstance(user_id, int) else None
    except JWTError:
        return
