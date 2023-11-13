from datetime import timedelta, datetime
from typing import Annotated
from http import HTTPStatus

from pydantic import EmailStr
from fastapi import HTTPException, UploadFile, APIRouter, Depends, Body

from app.schemas.response_schema import ErrorResponse
from app.models.user_model import User
from app.services import settings_service
from app.schemas import user_schema
from app.utils import img_utils
from app import deps

router = APIRouter(prefix="/settings", tags=["settings"])


@router.patch("/profile", response_model=user_schema.UserOut)
def update_profile(
    db: deps.DBDep,
    user: deps.AuthedUserDep,
    profile: user_schema.BaseUserProfile,
):
    return settings_service.update_settings_many(
        db,
        user,
        profile.model_dump(exclude_unset=True),
    )


@router.put(
    "/email",
    response_model=user_schema.UserOut,
    responses={
        HTTPStatus.CONFLICT: {
            "description": "Email taken",
            "model": ErrorResponse[str],
        },
    },
)
def change_email(
    db: deps.DBDep,
    user: Annotated[User, Depends(deps.AuthedUser(fresh=True))],
    config: deps.ConfigDep,
    new_email: Annotated[EmailStr, Body()],
):
    """
    Update the email and send an email verification.
    This will also unverify the user email.

    Requires a fresh JWT token.
    """

    return settings_service.update_setting_single(
        db,
        settings_service.EmailSetting(db, user, config.verification_url),
        new_email,
    )


@router.put("/password", response_model=user_schema.UserOut)
def change_password(
    db: deps.DBDep,
    user: Annotated[User, Depends(deps.AuthedUser(fresh=True))],
    new_password: Annotated[str, Body()],
):
    """Hash the password and update it. Requires a fresh JWT token."""

    return settings_service.update_setting_single(
        db,
        settings_service.PasswordSetting(user),
        new_password,
    )


@router.put(
    "/username",
    response_model=user_schema.UserOut,
    responses={
        HTTPStatus.CONFLICT: {
            "description": "Username taken",
            "model": ErrorResponse[str],
        },
        HTTPStatus.TOO_MANY_REQUESTS: {
            "description": "Username changed too recently",
            "model": ErrorResponse[str],
        },
    },
)
def change_username(
    db: deps.DBDep,
    user: deps.AuthedUserDep,
    config: deps.ConfigDep,
    new_username: Annotated[str, Body()],
):
    """Update the username"""

    return settings_service.update_setting_single(
        db,
        settings_service.UsernameSetting(
            db, user, timedelta(config.edit_username_every_days)
        ),
        new_username,
    )


@router.put(
    "/upload-profile-picture",
    responses={
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE: {
            "description": "Profile picture too large",
            "model": ErrorResponse[str],
        },
        HTTPStatus.BAD_REQUEST: {
            "description": "Bad image",
            "model": ErrorResponse[str],
        },
    },
)
async def upload_profile_picture(
    db: deps.DBDep,
    user: deps.AuthedUserDep,
    pfp: UploadFile,
):
    """
    Change a user's profile picture.
    The picture must be < 1mb and a valid image.
    """

    bytes = await pfp.read()
    if len(bytes) > 1024 * 1024:
        raise HTTPException(
            status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            detail="Profile picture cannot be bigger than 1mb",
        )

    img = img_utils.load_and_validate_image(bytes)
    img = img_utils.center_crop(img)
    await img_utils.save_pfp(user.user_id, img)

    user.pfp_last_changed = datetime.utcnow()
    db.commit()
