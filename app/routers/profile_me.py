from datetime import timedelta
from http import HTTPStatus
import os
import io

from fastapi import HTTPException, UploadFile, APIRouter
from PIL import Image
import aiofiles

from app.schemas.responses import ResponseError
from app.utils.common import get_or_create_uploads_folder
from app.schemas.user import UserSettings, UserOut
from app.dependencies import AuthedUserDep, SettingsDep, DBDep
from app.services import settings_service

router = APIRouter(tags=["profile-me"], prefix="/profile/me")


@router.patch("/change-settings", response_model=UserOut)
def change_settings(
    db: DBDep,
    user: AuthedUserDep,
    to_edit: UserSettings,
    settings: SettingsDep,
):
    special_updates: dict[str, settings_service.Setting] = {
        "username": settings_service.UsernameSetting(
            user,
            db,
            timedelta(days=settings.edit_username_every_days),
        ),
        "email": settings_service.EmailSetting(
            user,
            db,
            timedelta(days=settings.edit_email_every_days),
            settings.verification_url,
        ),
    }

    to_edit_changed = to_edit.model_dump(exclude_unset=True)
    for setting, new_value in to_edit_changed.items():
        if not setting in special_updates:
            setattr(user, setting, new_value)
            continue
        special_updates[setting].update(new_value)
    db.commit()

    return user


@router.put(
    "/upload-profile-picture",
    responses={
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE: {
            "description": "Profile picture too large",
            "model": ResponseError[str],
        },
        HTTPStatus.BAD_REQUEST: {
            "description": "Bad image",
            "model": ResponseError[str],
        },
    },
)
async def upload_profile_picture(user: AuthedUserDep, pfp: UploadFile):
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

    # Convert the uploaded file into a PIL object.
    # If the conversion fails, or img.verify fails, it means the image is bad.
    load_buffer = io.BytesIO(bytes)
    try:
        img = Image.open(load_buffer)
        img.verify()

        # A reopen is required after calling .verify()
        load_buffer.seek(0)
        img = Image.open(load_buffer)
    except:
        load_buffer.close()
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Bad image",
        )
    load_buffer.close()

    # Center crop the image
    width, height = img.size
    box_size = min(width, height)

    left = (width - box_size) / 2
    top = (height - box_size) / 2
    right = (width + box_size) / 2
    bottom = (height + box_size) / 2

    img = img.crop((left, top, right, bottom))  # type: ignore
    img = img.resize((160, 160))

    # Save image to buffer
    save_buffer = io.BytesIO()
    img.save(save_buffer, format="webp", quality=50)
    img.close()

    # Asynchronicity save the image
    profile_picture_path = os.path.join(
        get_or_create_uploads_folder(user.user_id),
        "profile-picture.webp",
    )
    async with aiofiles.open(profile_picture_path, "wb") as out_file:
        await out_file.write(save_buffer.getbuffer())

    save_buffer.close()
