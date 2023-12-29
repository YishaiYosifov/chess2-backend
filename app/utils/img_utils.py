from http import HTTPStatus
import os
import io

from fastapi import HTTPException
from PIL import Image
import aiofiles

from app.utils import common


def load_and_validate_image(img_bytes: bytes) -> Image.Image:
    """
    Load an image from a byte array, verify its integrity and return the image.

    :param img_bytes: the image bytes

    :return: the loaded image

    :raise HTTPException (BAD_REQUEST): the image could not be loaded
    """

    load_buffer = io.BytesIO(img_bytes)
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
    return img


def center_crop(img: Image.Image) -> Image.Image:
    """
    Center crop the image.
    Center cropping is cutting out the middle part of a picture and only keeping that part.

    :param image: the image to center crop

    :return: the center cropped image
    """

    width, height = img.size
    box_size = min(width, height)

    left = int((width - box_size) / 2)
    top = int((height - box_size) / 2)
    right = int((width + box_size) / 2)
    bottom = int((height + box_size) / 2)

    center_cropped = img.crop((left, top, right, bottom))
    center_cropped = center_cropped.resize((160, 160))

    return center_cropped


async def save_pfp(user_id: int, img: Image.Image) -> None:
    """
    Asynchronicity save the image save a profile picture in the correct place.

    :param user_id: the id of the profile picture owner user

    :param img: the profile picture
    """

    save_buffer = io.BytesIO()
    img.save(save_buffer, format="webp", quality=50)
    img.close()

    profile_picture_path = os.path.join(
        common.get_or_create_uploads_folder(user_id),
        "profile-picture.webp",
    )
    async with aiofiles.open(profile_picture_path, "wb") as out_file:
        await out_file.write(save_buffer.getbuffer())
    save_buffer.close()
