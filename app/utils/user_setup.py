from sqlalchemy.orm import Session

from app.models.rating_model import Rating
from app.models.user_model import User
from app.constants import enums


def create_default_ratings(db: Session, user: User):
    for variant in enums.Variant:
        db.add(Rating(user=user, variant=variant))
    db.commit()


def setup_user(db: Session, user: User):
    """Create the neccesary rows for a user"""

    create_default_ratings(db, user)
