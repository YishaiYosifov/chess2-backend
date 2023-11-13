from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, true

from app.models.rating_model import Rating
from app.models.user_model import User
from app.constants import enums


def fetch_many(
    db: Session,
    user: User,
    variants: list[enums.Variant],
) -> dict[str, Rating]:
    """
    Get the latest ratings for a user in a dictionary. If a rating doesn't exist, it will be inserted automatically

    :param db: the db session
    :param user: the user to get the ratings for
    :param variants: a list of variants
    :return: a dictionary containing all the ratings
    """

    ratings = db.execute(
        select(Rating).filter(
            (Rating.user == user)
            & (Rating.is_active == true())
            & (Rating.variant.in_(variants))
        )
    ).scalars()

    ratings_formatted: dict[str, Rating] = {
        rating.variant.value: rating for rating in ratings
    }

    # Check if a rating is missing. If it is, insert it into the db
    for variant in variants:
        if variant.value in ratings_formatted:
            continue

        rating = Rating(user=user, variant=variant)
        db.add(rating)
        db.flush()
        ratings_formatted[rating.variant.value] = rating
    db.commit()

    return ratings_formatted


def get_history(
    db: Session,
    user: User,
    since: datetime,
    variants: list[enums.Variant],
) -> dict[str, list[dict]]:
    """
    Fetch the history of a user's rating.

    :param db: the db session
    :param user: the user to fetch for
    :param since: the date to fetch since
    :param variants: a list of variants
    """

    rating_history = (
        db.execute(
            select(Rating)
            .filter(
                (Rating.user == user)
                & (Rating.variant.in_(variants))
                & (Rating.achieved_at >= since)
            )
            .order_by(Rating.achieved_at.desc())
        )
        .scalars()
        .all()
    )

    history_formatted = defaultdict(list)
    for rating in rating_history:
        history_formatted[rating.variant.value].append(rating)

    return history_formatted
