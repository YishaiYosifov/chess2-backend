from sqlalchemy.orm import Session

from app.constants.enums import Variants
from app.models.rating import Rating
from app.models.user import User


def create_default_ratings(db: Session, user: User):
    for variant in Variants:
        db.add(Rating(user=user, variant=variant))
    db.commit()


def setup_user(db: Session, user: User):
    """Create the neccesary rows for a user"""

    create_default_ratings(db, user)
