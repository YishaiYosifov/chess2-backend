from typing import Sequence
import math

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.games.game_results_model import GameResult
from app.models.user_model import User


def paginate_history(
    db: Session,
    user: User,
    page: int = 0,
    per_page: int = 10,
) -> Sequence[GameResult]:
    """
    Pageinate through game history for a specific page

    :param db: the db session
    :param user: the user to fetch the history of
    :param page: which page to fetch
    :param per_page: how many games to show per page
    :return: a list of games
    """

    games = (
        db.execute(
            select(GameResult)
            .filter((GameResult.user_white == user) | (GameResult.user_black == user))
            .order_by(GameResult.created_at.desc())
            .slice(page * per_page, page * per_page + per_page)
        )
        .scalars()
        .all()
    )

    return games


def page_count(db: Session, user: User, per_page: int) -> int:
    """
    Count how many pages are required to show all the games

    :param db: the db session
    :param user: the user to check for
    :param per_page: how many games to show per page
    :return: the page count
    """

    total = db.execute(
        select(func.count()).filter(
            (GameResult.user_white == user) | (GameResult.user_black == user)
        )
    ).scalar()
    return math.ceil((total or 0) / per_page)
