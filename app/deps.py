from dataclasses import dataclass
from typing import Generator, Annotated
from http import HTTPStatus

from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends, Path

from app.services.auth_service import oauth2_scheme
from app.models.user_model import User
from app.services import auth_service
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
ConfigDep = Annotated[Settings, Depends(get_settings)]


@dataclass(frozen=True, eq=True)
class AuthedUser:
    required: bool = True
    refresh: bool = False
    fresh: bool = False

    def __call__(
        self,
        db: DBDep,
        config: ConfigDep,
        token: Annotated[str, Depends(oauth2_scheme)],
    ) -> User | None:
        """Dependency to fetch the authorized user"""

        credentials_exception = HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not token and self.required:
            raise credentials_exception
        elif not token:
            return

        user = user_crud.fetch_by_token(
            db,
            config.secret_key,
            config.jwt_algorithm,
            token,
            self.refresh,
            self.fresh,
        )
        if not user:
            raise credentials_exception

        return user


AuthedUserDep = Annotated[User, Depends(AuthedUser())]


def target_or_me(
    db: DBDep,
    target: Annotated[str, Path()],
    config: ConfigDep,
    token: Annotated[str, Depends(auth_service.oauth2_scheme)],
) -> User:
    """
    Dependency to fetch a target user.
    If the target is `me`, it will fetch the currently logged in user.
    The target user is defined as a path parameter.

    :raise HTTPException (Not Found): the target user was not found
    """

    if target == "me":
        user = (
            user_crud.fetch_by_token(
                db,
                config.secret_key,
                config.jwt_algorithm,
                token,
            )
            if token
            else None
        )
    else:
        user = user_crud.generic_fetch(db, target)

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"User not found: {target}",
        )

    return user


TargetOrMeDep = Annotated[User, Depends(target_or_me)]
