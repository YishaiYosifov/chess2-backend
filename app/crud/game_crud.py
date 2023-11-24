from typing import Sequence

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


def total(db: Session, user: User) -> int:
    """
    Count the total number of games the user has played

    :param db: the db session
    :param user: the user to check for
    """

    total = db.execute(
        select(func.count(GameResult.game_results_id)).filter(
            (GameResult.user_white == user) | (GameResult.user_black == user)
        )
    ).scalar()
    return total or 0
