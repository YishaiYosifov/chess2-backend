import shutil
import os

from sqlalchemy.orm import Session

from app.constants.enums import Variants
from app.models.rating import Rating
from app.utils.common import get_uploads_path
from app.models.user import User


def create_default_ratings(db: Session, user: User):
    for variant in Variants:
        db.add(Rating(user=user, variant=variant))
    db.commit()


def create_default_files(user: User):
    """Create the uploads folder"""

    uploads_folder = get_uploads_path(user.user_id)
    if os.path.exists(uploads_folder):
        shutil.rmtree(uploads_folder)
    os.makedirs(uploads_folder)


def setup_user(db: Session, user: User):
    """Create the neccesary rows and files for a user"""

    create_default_files(user)
    create_default_ratings(db, user)
