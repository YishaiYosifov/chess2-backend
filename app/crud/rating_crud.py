from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import select, true, func

from app.schemas.config_schema import CONFIG
from app.models.rating_model import Rating
from app.models.user_model import AuthedUser
from app.constants import enums


def fetch_single(
    db: Session,
    user: AuthedUser,
    variant: enums.Variant,
) -> Rating | None:
    """
    Get a user's latest rating.

    :param db: the database session
    :param user: the user to fetch the rating for
    :param variant: the rating variant to fetch

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


def fetch_rating_elo(
    db: Session,
    user: AuthedUser,
    variant: enums.Variant,
    default: int = CONFIG.default_rating,
) -> int:
    """
    Get the user's latest rating elo value.

    Used in cases where the elo value is required but
    the rating model object isn't so important.

    :param db: the database session
    :param user: the user to fetch the elo for
    :param variant: the rating variant to fetch
    :param default: what to return when the user doesn't have a rating.
                    defaults to the `default_rating` value in the config.

    :return: the elo if the rating exists or the default value
    """

    rating = fetch_single(db, user, variant)
    if not rating:
        return default
    return rating.elo


def fetch_many(
    db: Session,
    user: AuthedUser,
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
    user: AuthedUser,
    since: date,
    variants: list[enums.Variant],
) -> dict[enums.Variant, list[Rating]]:
    """
    Fetch the history of a user's rating.

    :param db: the database session
    :param user: the user for whom to fetch for
    :param since: the date to fetch since
    :param variants: a list of variants

    :return: a dictionary containing the variants their list of
    ratings in ascending order (from least to most recent)
    """

    rating_history = (
        db.execute(
            select(Rating)
            .filter(
                (Rating.user == user)
                & (Rating.variant.in_(variants))
                & (Rating.achieved_at >= since)
            )
            .order_by(Rating.achieved_at)
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
    user: AuthedUser,
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
