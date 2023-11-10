from datetime import timedelta, datetime
from typing import Any
import uuid
import time

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import select
from jose import jwt, JWTError

from app.models.jti_blocklist import JTIBlocklist

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# region encode jwt


def _encode_jwt_token(
    secret_key: str,
    jwt_algorithm,
    data: dict,
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
        {"sub": str(user_id), "type": "access"},
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


def decode_access_token(secret_key: str, jwt_algorithm: str, token: str) -> int | None:
    """
    Try to decode an access token into a user id

    :param secret_key: the secret key to sign the token with
    :param jwt_algorithm: which algorithm to use to generate the key
    :param token: the jwt token
    :return: the user id if decoding was successful, otherwise None
    """

    payload = _decode_jwt_token(secret_key, jwt_algorithm, token)
    if payload.get("type") != "access":
        return

    return _get_jwt_indentity(payload)


def _check_token_revocation(db: Session, payload: dict[str, Any]) -> bool:
    """
    Check if the token jti is blocklisted

    :param db: an sqlalchemy session to check for revocation in
    :param payload: the decoded payload returned from the jwt token
    :return: whether the token is revoked
    """

    return db.execute(select(JTIBlocklist).filter_by(jti=payload.get("jti"))).scalar()


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

    payload = _decode_jwt_token(secret_key, jwt_algorithm, token, {"require_jti": True})
    if payload.get("type") != "refresh" or _check_token_revocation(db, payload):
        return

    return _get_jwt_indentity(payload)


# endregion
