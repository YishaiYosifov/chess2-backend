from datetime import timedelta, datetime
from typing import TypeVar
from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy import select, ColumnExpressionArgument
from fastapi import HTTPException

from app.services import auth_service, jwt_service
from app.models import user_model
from app.utils import common

from ..schemas import user_schema

T = TypeVar("T", bound=user_model.User)


def _fetch_by(
    db: Session,
    criteria: ColumnExpressionArgument[bool],
    model: type[T] = user_model.User,
) -> T | None:
    return db.execute(select(model).filter(criteria)).scalar()


def get_user(
    db: Session,
    selector: int | str,
    model: type[T] = user_model.User,
) -> T | None:
    """Fetch a user by a username / id"""

    return (
        get_by_id(db, int(selector), model)
        if isinstance(selector, int) or selector.isnumeric()
        else get_by_username(db, selector, model)
    )


def get_by_id(
    db: Session,
    user_id: int,
    model: type[T] = user_model.User,
) -> T | None:
    """Get a user by their user id from a specific model"""

    return _fetch_by(db, model.user_id == user_id, model)


def get_by_username(
    db: Session,
    username: str,
    model: type[T] = user_model.User,
) -> T | None:
    """Get a user by their username from a specific model"""

    return _fetch_by(db, model.username == username, model)


def get_by_email(db: Session, email: str) -> user_model.AuthedUser | None:
    """Get a user by their email from a specific model"""

    return _fetch_by(
        db,
        user_model.AuthedUser.email == email,
        user_model.AuthedUser,
    )


def unique_email_or_raise(db: Session, email: str) -> None:
    """Make sure an email is unique or raise an HTTP conflict exception"""

    if get_by_email(db, email):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"email": "Email taken"},
        )


def unique_username_or_raise(db: Session, username: str) -> None:
    """Make sure an username is unique or raise an HTTP conflict exception"""

    if get_by_username(db, username):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"username": "Username taken"},
        )


def get_by_token(
    db: Session,
    secret_key: str,
    jwt_algorithm: str,
    token: str,
    refresh: bool = False,
    fresh: bool = False,
    model: type[T] = user_model.AuthedUser,
) -> T | None:
    """
    Try to decode a jwt token into a user model

    :param db: the database session to fetch the user with
    :param secret_key: the secret key to sign the token with
    :param jwt_algorithm: which algorithm to use to generate the key
    :param token: the jwt token
    :param refresh: whether to require a refresh token
    :param fresh: whether to require a fresh token
    :param model: which user model to fetch. defaults to AuthedUser

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

    return get_user(db, user_id, model)


def authenticate(
    db: Session, username: str, password: str
) -> user_model.AuthedUser | None:
    """
    Get a user by their username and password.
    Will return None if the username was not found or the password was incorrect.
    """

    user = get_by_username(db, username, user_model.AuthedUser)
    if not user or not auth_service.verify_password(
        password, user.hashed_password
    ):
        return

    return user


def create_authed(
    db: Session,
    user: user_schema.UserIn,
) -> user_model.AuthedUser:
    """Hash the password and create an authed user"""

    hashed_password = auth_service.hash_password(user.password)
    db_user = user_model.AuthedUser(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)

    return db_user


def create_guest(db: Session) -> user_model.GuestUser:
    """Create a guest user with a unique username"""

    token = common.truncated_uuid()
    while get_by_username(db, f"Guest-{token}"):
        token = common.truncated_uuid()

    guest = user_model.GuestUser(username=f"Guest-{token}")
    db.add(guest)

    return guest


def delete_inactive_guests(db: Session, delete_minutes: int):
    """
    Delete all inactive guest accounts. This functions commits at the end

    :param db: the database session
    :param delete_minutes: how long do the accounts need to be inactive in minutes to delete
    """

    delete_from = datetime.utcnow() - timedelta(minutes=delete_minutes)

    guests = db.execute(
        select(user_model.GuestUser).filter(
            user_model.GuestUser.last_refreshed_token <= delete_from,
        )
    ).scalars()

    # this loops over every guest and manually deletes them to
    # cascade the deletion to relationships
    for guest in guests:
        db.delete(guest)

    db.commit()
