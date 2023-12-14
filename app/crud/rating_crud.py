from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import select, true, func

from app.models.rating_model import Rating
from app.models.user_model import User
from app.constants import enums


def fetch_single(
    db: Session, user: User, variant: enums.Variant
) -> Rating | None:
    """
    Get a user's latest rating.

    :param user: the user the get the rating for
    :param variant: the variant to get
    :return: the rating object, or None if it was not found
    """

    rating = db.execute(
        select(Rating).filter_by(
            user=user,
            is_active=True,
            variant=variant,
        )
    ).scalar()
    return rating


def fetch_many(
    db: Session,
    user: User,
    variants: list[enums.Variant],
) -> dict[enums.Variant, Rating]:
    """
    Get the latest ratings for a user in a dictionary.

    :param db: the database session
    :param user: the user for whom to fetch for
    :param variants: a list of variants
    :return: a dictionary containing all the current ratings
    """

    ratings = db.execute(
        select(Rating).filter(
            (Rating.user == user)
            & (Rating.is_active == true())
            & (Rating.variant.in_(variants))
        )
    ).scalars()

    return {rating.variant: rating for rating in ratings}


def fetch_history(
    db: Session,
    user: User,
    since: date,
    variants: list[enums.Variant],
) -> dict[enums.Variant, list[Rating]]:
    """
    Fetch the history of a user's rating.

    :param db: the database session
    :param user: the user for whom to fetch for
    :param since: the date to fetch since
    :param variants: a list of variants
    :return: a dictionary containing the variants their list of ratings
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

    history_formatted = defaultdict(list[Rating])
    for rating in rating_history:
        history_formatted[rating.variant].append(rating)
    return history_formatted


def fetch_min_max(
    db: Session,
    user: User,
    variants: list[enums.Variant],
) -> dict[enums.Variant, tuple[int, int]]:
    """
    Find the highest and lowest elo for a user

    :param db: the database session
    :param user: the user for whom to fetch for
    :param variants: a list of the variants to search
    :return: a dictionary containing the variants as a key and min, max as a tuple value
    """

    minmax = db.execute(
        select(Rating.variant, func.min(Rating.elo), func.max(Rating.elo))
        .filter((Rating.user == user) & Rating.variant.in_(variants))
        .group_by(Rating.variant)
    ).all()

    return {
        variant: (
            min_rating,
            max_rating,
        )
        for variant, min_rating, max_rating in minmax
    }
