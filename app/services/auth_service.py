from datetime import timedelta, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from jose import jwt

from app.models.user import User

from ..crud.user_crud import fetch_user_by_selector

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


async def authenticate_user(
    db: AsyncSession,
    selector: str,
    password: str,
) -> User | None:
    user = await fetch_user_by_selector(db, selector)
    if not user:
        return
    if not verify_password(password, user.hashed_password):
        return
    return user


def create_access_token(
    secret_key: str,
    algorithm: str,
    data: dict,
    expires_in_minutes: int = 30,
) -> str:
    """
    Generate a JWT access token

    :param secret_key: the app secret key to encode the token with
    :param algorithm: the algrithm to encode with
    :param data: what data should be encoded (usually looks something like `{"sub": ...}`)
    :param expires_in_minutes: when should this token expires
    :return: the encoded jwt access token
    """

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt
