from sqlalchemy.orm import Session
from sqlalchemy import select, ColumnExpressionArgument

from app.services.auth_service import verify_password, hash_password
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
