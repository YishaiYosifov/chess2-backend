from sqlalchemy.orm import joinedload, Session
from sqlalchemy import select

from app.services.auth_service import verify_password, hash_password
from app.models.user import User as UserModel

from ..schemes import user as user_schema


def fetch_user_by_selector(db: Session, selector: str) -> UserModel | None:
    """Fetch a user by their username / email"""

    return db.execute(
        select(UserModel)
        .options(
            joinedload(UserModel.ratings),
            joinedload(UserModel.game_request),
            joinedload(UserModel.incoming_games),
            joinedload(UserModel.player),
        )
        .filter((UserModel.username == selector) | (UserModel.email == selector))
    ).scalar()


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


async def auth_user(
    db: Session,
    selector: str,
    password: str,
) -> UserModel | None:
    user = fetch_user_by_selector(db, selector)
    if not user:
        return
    if not verify_password(password, user.hashed_password):
        return

    return user
