import time

from sqlalchemy.orm import Session

from app.models.user_model import GuestUser
from app.services import jwt_service


def fetch_by_id(db: Session, user_id: int):
    pass


def create_guest(db: Session) -> GuestUser:
    GuestUser(username=f"guest-{time.time()}")


def fetch_or_create_guest_by_token(
    db: Session,
    secret_key: str,
    jwt_algorithm: str,
    token: str,
):
    user_id = jwt_service.decode_access_token(secret_key, jwt_algorithm, token)
    if not user_id:
        return
