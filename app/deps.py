from dataclasses import dataclass
from typing import Generator, Annotated
from http import HTTPStatus

from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends, Path

from app.services.auth_service import oauth2_scheme
from app.models.user_model import AuthedUser
from app.services import auth_service
from app.schemas import user_schema
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
class GetAuthedUser:
    required: bool = True
    refresh: bool = False
    fresh: bool = False

    def __call__(
        self,
        db: DBDep,
        config: ConfigDep,
        tokens: Annotated[user_schema.AuthTokens, Depends(oauth2_scheme)],
    ) -> AuthedUser | None:
        """Dependency to fetch the authorized user"""

        credentials_exception = HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        token = tokens.refresh_token if self.refresh else tokens.access_token

        if not token and self.required:
            raise credentials_exception
        elif not token:
            return

        # Try to fetch the user with the token
        user = user_crud.fetch_authed_by_token(
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


AuthedUserDep = Annotated[AuthedUser, Depends(GetAuthedUser())]


def target_or_me(
    db: DBDep,
    target: Annotated[str, Path()],
    config: ConfigDep,
    tokens: Annotated[
        user_schema.AuthTokens, Depends(auth_service.oauth2_scheme)
    ],
) -> AuthedUser:
    """
    Dependency to fetch a target user.
    If the target is `me`, it will fetch the currently logged in user.
    The target user is defined as a path parameter.

    :raise HTTPException (Not Found): the target user was not found
    """

    if target == "me":
        user = (
            user_crud.fetch_authed_by_token(
                db,
                config.secret_key,
                config.jwt_algorithm,
                tokens.access_token,
            )
            if tokens.access_token
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


TargetOrMeDep = Annotated[AuthedUser, Depends(target_or_me)]
