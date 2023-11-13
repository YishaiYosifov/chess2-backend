from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy import select, ColumnExpressionArgument
from fastapi import HTTPException

from app.services.auth_service import verify_password, hash_password
from app.models.user_model import User as UserModel

from ..schemas import user_schema


def fetch_by(
    db: Session, *criteria: ColumnExpressionArgument[bool]
) -> UserModel | None:
    return db.execute(select(UserModel).filter(*criteria)).scalar()


def original_email_or_raise(db: Session, email: str) -> None:
    if fetch_by(db, UserModel.email == email):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Email taken",
        )


def original_username_or_raise(db: Session, username: str) -> None:
    if fetch_by(db, UserModel.username == username):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Username taken",
        )


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
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
