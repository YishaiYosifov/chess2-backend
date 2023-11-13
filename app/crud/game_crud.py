from typing import Sequence

from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.games.game_results_model import GameResult
from app.models.user_model import User


def fetch_history(db: Session, user: User, limit: int = 10) -> Sequence[GameResult]:
    """
    Fetch the past game results for a user.
    The user can be either the black or white player.

    :param db: the db session
    :param user: the user to fetch the history of
    :param limit: how many games to fetch
    """

    games = (
        db.execute(
            select(GameResult)
            .filter((GameResult.user_white == user) | (GameResult.user_black == user))
            .order_by(desc(GameResult.created_at))
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return games
