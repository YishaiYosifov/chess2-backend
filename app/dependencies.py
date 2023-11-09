from typing import Annotated
from http import HTTPStatus

from sqlalchemy.orm import Session
from fastapi import HTTPException, Security, Depends

from app.services.auth_service import (
    decode_refresh_token,
    decode_access_token,
    oauth2_scheme,
)
from app.models.user import User
from app.crud import user_crud

from .schemas.config import get_settings, Settings
from .db import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


class AuthedUser:
    def __init__(self, refresh: bool = False) -> None:
        self.refresh = refresh

    def __call__(
        self,
        db: DBDep,
        token: Annotated[str, Depends(oauth2_scheme)],
    ) -> User | None:
        """Dependency to fetch the authorized user"""

        # Common exception to raise when the user is found to not be authorized
        credentials_exception = HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        user_id = (
            decode_refresh_token(db, token)
            if self.refresh
            else decode_access_token(token)
        )
        if not user_id:
            raise credentials_exception

        user = user_crud.generic_fetch(db, user_id)
        if user is None:
            raise credentials_exception
        return user


AuthedUserRefreshDep = Annotated[User, Security(AuthedUser(refresh=True))]
AuthedUserDep = Annotated[User, Security(AuthedUser())]
