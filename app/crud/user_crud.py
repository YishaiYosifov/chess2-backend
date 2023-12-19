from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy import select, ColumnExpressionArgument
from fastapi import HTTPException

from app.models.user_model import AuthedUser as UserModel
from app.services import auth_service, jwt_service

from ..schemas import user_schema


def fetch_by(
    db: Session, *criteria: ColumnExpressionArgument[bool]
) -> UserModel | None:
    return db.execute(select(UserModel).filter(*criteria)).scalar()


def original_email_or_raise(db: Session, email: str) -> None:
    if fetch_by(db, UserModel.email == email):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"email": "Email taken"},
        )


def original_username_or_raise(db: Session, username: str) -> None:
    if fetch_by(db, UserModel.username == username):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"username": "Username taken"},
        )


def fetch_authed_by_token(
    db: Session,
    secret_key: str,
    jwt_algorithm: str,
    token: str,
    refresh: bool = False,
    fresh: bool = False,
) -> UserModel | None:
    """
    Try to decode a jwt token into a user model

    :param db: the database session to fetch the user with
    :param secret_key: the secret key to sign the token with
    :param jwt_algorithm: which algorithm to use to generate the key
    :param token: the jwt token
    :param refresh: whether to require a refresh token
    :param fresh: whether to require a fresh token
    :return: the user model if decoding was successful, otherwise None
    """

    user_id = (
        jwt_service.decode_refresh_token(
            secret_key,
            jwt_algorithm,
            db,
            token,
        )
        if refresh
        else jwt_service.decode_access_token(
            secret_key,
            jwt_algorithm,
            token,
            fresh,
        )
    )
    if not user_id:
        return

    user = generic_fetch(db, user_id)
    return user


def generic_fetch(db: Session, selector: int | str) -> UserModel | None:
    """Fetch user by their username / id"""

    return (
        db.get(
            UserModel,
            selector,
        )
        if isinstance(selector, int)
        else db.execute(select(UserModel).filter_by(username=selector)).scalar()
    )


def authenticate(db: Session, username: str, password: str) -> UserModel | None:
    user = fetch_by(db, UserModel.username == username)
    if not user:
        return
    if not auth_service.verify_password(password, user.hashed_password):
        return
    return user


def create_user(
    db: Session,
    user: user_schema.UserIn,
) -> UserModel:
    hashed_password = auth_service.hash_password(user.password)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)

    return db_user
