from datetime import datetime
from typing import Annotated
from http import HTTPStatus

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import BackgroundTasks, HTTPException, APIRouter, Response, Depends

from app.utils.email_verification import send_verification_email
from app.models.user_model import AuthedUser
from app.websockets import ws_server_instance
from app.services import auth_service, jwt_service
from app.schemas import response_schema, user_schema
from app.crud import user_crud
from app import deps

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=user_schema.PrivateUserOut,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.CONFLICT: {
            "description": "Username / email already taken",
            "model": response_schema.ErrorResponse[dict[str, str]],
        }
    },
)
def signup(
    user: user_schema.UserIn,
    db: deps.DBDep,
    background_tasks: BackgroundTasks,
    config: deps.ConfigDep,
):
    """
    Takes a username, email and password and creates registers a new user.
    This path operation will also send a verification email.
    """

    user_crud.unique_username_or_raise(db, user.username)
    user_crud.unique_email_or_raise(db, user.email)

    db_user = user_crud.create_authed(db, user)
    db.commit()

    if config.send_verification_email:
        background_tasks.add_task(
            send_verification_email,
            email=db_user.email,
            verification_url=config.verification_url,
        )

    return db_user


@router.post("/login", response_model=user_schema.AuthTokens)
def login(
    db: deps.DBDep,
    config: deps.ConfigDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
):
    """Authenticates a user by generating a jwt access and refresh token if the credentials match."""

    user = user_crud.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Incorrect username / password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = jwt_service.create_access_token(
        config.secret_key,
        config.jwt_algorithm,
        user.user_id,
        expires_in_minutes=config.access_token_expires_minutes,
        fresh=True,
    )
    refresh_token = jwt_service.create_refresh_token(
        config.secret_key,
        config.jwt_algorithm,
        user.user_id,
        expires_in_days=config.refresh_token_expires_days,
    )

    auth_service.set_auth_cookies(
        response,
        access_token,
        refresh_token,
        access_token_max_age=config.access_token_expires_minutes * 60,
        refresh_token_max_age=config.refresh_token_expires_days * 60 * 60 * 24,
    )

    return user_schema.AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/logout")
def logout(response: Response):
    """Remove all auth cookies"""

    auth_service.remove_auth_cookies(response)


@router.get("/refresh-access-token", response_model=user_schema.AccessToken)
def refresh_access_token(
    user: Annotated[AuthedUser, Depends(deps.GetCurrentUser(refresh=True))],
    config: deps.ConfigDep,
    response: Response,
):
    """Generate a new access token using a refresh token"""

    access_token = jwt_service.create_access_token(
        config.secret_key,
        config.jwt_algorithm,
        user.user_id,
        expires_in_minutes=config.access_token_expires_minutes,
    )
    auth_service.set_auth_cookies(
        response,
        access_token=access_token,
        access_token_max_age=config.access_token_expires_minutes * 60,
    )
    user.last_refreshed_token = datetime.utcnow()

    return user_schema.AccessToken(access_token=access_token)


@router.get(
    "/guest-account",
    response_model=user_schema.AccessToken,
    status_code=HTTPStatus.CREATED,
)
def create_guest_account(db: deps.DBDep, config: deps.ConfigDep):
    """
    Create a new guest account and get its access token.
    Keep in mind the account is temporary and is bound to be deleted.
    """

    guest = user_crud.create_guest(db)
    db.commit()

    access_token = jwt_service.create_access_token(
        config.secret_key,
        config.jwt_algorithm,
        guest.user_id,
        expires_in_minutes=config.access_token_expires_minutes,
    )

    return user_schema.AccessToken(access_token=access_token)


@router.get("/test")
async def test():
    await ws_server_instance.emit({}, 1)
