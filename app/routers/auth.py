from typing import Annotated
from http import HTTPStatus

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import BackgroundTasks, HTTPException, APIRouter, Depends

from app.utils.email_verification import send_verification_email
from app.services.auth_service import create_refresh_token, create_access_token
from app.schemas.responses import ResponseError, AccessToken, AuthTokens
from app.utils.user_setup import setup_user
from app.schemas.user import UserOut, UserIn
from app.dependencies import AuthedUserRefreshDep, SettingsDep, DBDep
from app.crud import user_crud

router = APIRouter(tags=["auth"], prefix="/auth")


@router.post(
    "/signup",
    response_model=UserOut,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.CONFLICT: {
            "description": "Username / email already taken",
            "model": ResponseError[dict[str, str]],
        }
    },
)
def signup(
    user: UserIn,
    db: DBDep,
    background_tasks: BackgroundTasks,
    settings: SettingsDep,
):
    """
    Takes a username, email and password and creates registers a new user.

    This path operation will also:
    - send a verification email
    - create the necessary files
    """

    if user_crud.fetch_by_username(db, user.username):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"username": "Username taken"},
        )
    elif user_crud.fetch_by_email(db, user.email):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"email": "Email taken"},
        )

    db_user = user_crud.create_user(db, user)
    if settings.send_verification_email:
        background_tasks.add_task(send_verification_email, user=db_user)

    setup_user(db, db_user)

    return db_user


@router.post("/login", response_model=AuthTokens)
def login(
    db: DBDep,
    settings: SettingsDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Authenticates a user by generating a jwt access and refresh token if the credentials match."""

    user = user_crud.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Incorrect username / password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user.user_id,
        expires_in_minutes=settings.access_token_expires_minutes,
    )
    refresh_token = create_refresh_token(
        user.user_id,
        expires_in_days=settings.refresh_token_expires_days,
    )
    return AuthTokens(access_token=access_token, refresh_token=refresh_token)


@router.get("/refresh-access-token", response_model=AccessToken)
def refresh_access_token(user: AuthedUserRefreshDep, settings: SettingsDep):
    """Generate a new access token using a refresh token"""

    access_token = create_access_token(
        user.user_id,
        expires_in_minutes=settings.access_token_expires_minutes,
    )
    return AccessToken(access_token=access_token)
