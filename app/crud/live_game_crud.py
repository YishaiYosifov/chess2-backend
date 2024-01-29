from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.games.live_game_model import LiveGame


def fetch_live_game(db: Session, token: str):
    return db.execute(select(LiveGame).filter_by(token=token)).scalar()
