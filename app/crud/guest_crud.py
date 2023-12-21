from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user_model import GuestUser
from app.services import jwt_service
from app.utils import common


def username_token_exists(db: Session, token: str) -> bool:
    username = f"Guest-{token}"
    return (
        db.execute(select(GuestUser).filter_by(username=username)).scalar()
        is not None
    )


def create_guest(db: Session) -> GuestUser:
    """Create a guest user with a unique username"""

    token = common.truncated_uuid()
    while username_token_exists(db, token):
        token = common.truncated_uuid()

    guest = GuestUser(username=f"Guest-{token}")
    db.add(guest)
    return guest


def fetch_or_create_guest_by_token(
    db: Session,
    secret_key: str,
    jwt_algorithm: str,
    token: str,
):
    user_id = jwt_service.decode_access_token(secret_key, jwt_algorithm, token)
    if not user_id:
        return
