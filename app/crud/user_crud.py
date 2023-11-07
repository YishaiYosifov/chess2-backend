from typing import Annotated
from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy import select, ColumnExpressionArgument
from fastapi import HTTPException, Depends

from app.services.auth_service import (
    decode_access_token,
    verify_password,
    oauth2_scheme,
    hash_password,
)
from app.dependencies import DBDep
from app.models.user import User as UserModel

from ..schemas import user as user_schema


def fetch_by(db: Session, *criteria: ColumnExpressionArgument[bool]):
    return db.execute(select(UserModel).filter(*criteria)).scalar()


def fetch_by_email(db: Session, email: str) -> UserModel | None:
    return fetch_by(db, UserModel.email == email)


def fetch_by_username(db: Session, username: str) -> UserModel | None:
    return fetch_by(db, UserModel.username == username)


def generic_fetch(db: Session, selector: int | str):
    """Fetch user by their username / id"""

    return (
        db.get(
            UserModel,
            selector,
        )
        if isinstance(selector, int)
        else db.execute(select(UserModel).filter_by(username=selector)).scalar()
    )


async def fetch_authed(
    db: DBDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserModel | None:
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = decode_access_token(token)
    if not user_id:
        raise credentials_exception

    user = db.get(UserModel, user_id)
    if user is None:
        raise credentials_exception
    return user


def authenticate(db: Session, username: str, password: str) -> UserModel | None:
    user = fetch_by_username(db, username)
    if not user:
        return
    if not verify_password(password, user.hashed_password):
        return
    return user


def create_user(
    db: Session,
    user: user_schema.UserIn,
) -> UserModel:
    hashed_password = hash_password(user.password)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        country=str(user.country).lower() if user.country else None,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
