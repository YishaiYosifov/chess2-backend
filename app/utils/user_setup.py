import shutil
import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rating import Rating
from app.utils.common import get_uploads_path
from app.models.user import User
from app.enums import Variants


def create_default_ratings(db: AsyncSession, user: User):
    for variant in Variants:
        db.add(Rating(user=user, variant=variant))


def create_default_files(user: User):
    """Create the uploads folder"""

    uploads_folder = get_uploads_path(user.user_id)
    if os.path.exists(uploads_folder):
        shutil.rmtree(uploads_folder)
    os.makedirs(uploads_folder)


def setup_user(db: AsyncSession, user: User):
    """Create the neccesary rows and files for a user"""

    create_default_files(user)
    create_default_ratings(db, user)
