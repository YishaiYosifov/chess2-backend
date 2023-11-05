from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.auth_service import hash_password
from app.models.user import User as UserModel

from ..schemes import user as user_schema


async def fetch_user_by_selector(db: AsyncSession, selector: str) -> UserModel | None:
    """Fetch a user by their username / email"""

    return (
        await db.execute(
            select(UserModel).filter(
                (UserModel.username == selector) | (UserModel.email == selector)
            )
        )
    ).scalar()


async def create_user(
    db: AsyncSession,
    user: user_schema.UserIn,
    do_setup: bool = True,
) -> UserModel:
    hashed_password = hash_password(user.password)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        country=user.country,
    )
    db.add(db_user)
    await db.commit()

    return db_user
