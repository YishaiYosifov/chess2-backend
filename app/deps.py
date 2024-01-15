from typing import Generator, Annotated
from http import HTTPStatus

from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends, Path

from app.services.auth_service import oauth2_scheme
from app.models.user_model import AuthedUser, GuestUser, User
from app.schemas import user_schema
from app.crud import user_crud

from .schemas.config_schema import get_config, Config
from .db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBDep = Annotated[Session, Depends(get_db)]
ConfigDep = Annotated[Config, Depends(get_config)]
TokensDep = Annotated[user_schema.AuthTokens, Depends(oauth2_scheme)]


class GetCurrentUser:
    def __init__(
        self,
        authed: bool = True,
        required: bool = True,
        refresh: bool = False,
        fresh: bool = False,
    ) -> None:
        self.authed = authed
        self.required = required
        self.refresh = refresh
        self.fresh = fresh

    def get_authed_user(
        self,
        db: Session,
        tokens: user_schema.AuthTokens,
        secret_key: str,
        jwt_algorithm: str,
    ) -> AuthedUser | None:
        token = tokens.refresh_token if self.refresh else tokens.access_token
        if not token:
            return

        # Try to fetch the user with the token
        user = user_crud.get_by_token(
            db,
            secret_key,
            jwt_algorithm,
            token,
            self.refresh,
            self.fresh,
        )

        return user

    def get_unauthed_user(
        self,
        db: Session,
        tokens: user_schema.AuthTokens,
        secret_key: str,
        jwt_algorithm: str,
    ) -> User | None:
        if not tokens.access_token:
            return

        return user_crud.get_by_token(
            db,
            secret_key,
            jwt_algorithm,
            tokens.access_token,
            model=User,
        )

    def __call__(
        self,
        db: DBDep,
        config: ConfigDep,
        tokens: TokensDep,
    ) -> User | None:
        """Dependency to fetch the authorized user"""

        user = (
            self.get_authed_user(
                db,
                tokens,
                config.secret_key,
                config.jwt_algorithm,
            )
            if self.authed
            else self.get_unauthed_user(
                db,
                tokens,
                config.secret_key,
                config.jwt_algorithm,
            )
        )

        if not user and self.required:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user


AuthedUserDep = Annotated[AuthedUser, Depends(GetCurrentUser())]
UnauthedUserDep = Annotated[GuestUser, Depends(GetCurrentUser(authed=False))]


def target_or_me(
    db: DBDep,
    target: Annotated[str, Path()],
    config: ConfigDep,
    tokens: TokensDep,
) -> AuthedUser:
    """
    Dependency to fetch a target user.
    If the target is `me`, it will fetch the currently logged in user.
    The target user is defined as a path parameter.
    """

    if target == "me":
        user = (
            user_crud.get_by_token(
                db,
                config.secret_key,
                config.jwt_algorithm,
                tokens.access_token,
            )
            if tokens.access_token
            else None
        )
    else:
        user = user_crud.get_user(db, target, AuthedUser)

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"User not found: {target}",
        )

    return user


TargetOrMeDep = Annotated[AuthedUser, Depends(target_or_me)]
