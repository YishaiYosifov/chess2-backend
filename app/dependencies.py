from typing import Generator, Annotated
from http import HTTPStatus

from sqlalchemy.orm import Session
from fastapi import HTTPException, Security, Depends

from app.services.auth_service import (
    decode_refresh_token,
    decode_access_token,
    oauth2_scheme,
)
from app.models.user_model import User
from app.crud import user_crud

from .schemas.config_schema import get_settings, Settings
from .db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


class AuthedUser:
    def __init__(self, refresh: bool = False, fresh: bool = False) -> None:
        self.refresh = refresh
        self.fresh = fresh

    def __call__(
        self,
        db: DBDep,
        settings: SettingsDep,
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
            decode_refresh_token(
                settings.secret_key,
                settings.jwt_algorithm,
                db,
                token,
            )
            if self.refresh
            else decode_access_token(
                settings.secret_key,
                settings.jwt_algorithm,
                token,
            )
        )
        if not user_id:
            raise credentials_exception

        user = user_crud.generic_fetch(db, user_id)
        if user is None:
            raise credentials_exception
        user.is_fresh = True

        return user


authed_user_refresh = AuthedUser(refresh=True)
authed_user_fresh = AuthedUser(fresh=True)
authed_user = AuthedUser()

AuthedUserRefreshDep = Annotated[User, Security(authed_user_refresh)]
FreshAuthedUserDep = Annotated[User, Security(authed_user_fresh)]
AuthedUserDep = Annotated[User, Security(authed_user)]
