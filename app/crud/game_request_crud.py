from sqlalchemy.orm import Session
from sqlalchemy import literal, select, func

from app.models.games.game_request_model import GameRequest
from app.schemas.config_schema import CONFIG
from app.models.rating_model import Rating
from app.models.user_model import User
from app.schemas import game_schema
from app import enums


# TODO: write test auhhh
def create_game_request(
    db: Session,
    user: User,
    game_settings: game_schema.GameSettings,
) -> GameRequest:
    game_request = GameRequest(
        inviter=user,
        variant=game_settings.variant,
        time_control=game_settings.time_control,
        increment=game_settings.increment,
    )
    db.add(game_request)
    return game_request


def search_game_request(
    db: Session,
    game_settings: game_schema.GameSettings,
    rating: int | None = None,
    user_type: enums.UserType = enums.UserType.AUTHED,
):
    """
    Search for a game without a specified recipient that fits these conditions:
        - same settings (variant, time control and increment)
        - the inviter's rating is in the acceptable rating difference from the provided rating.
          If the inviter doesn't have a rating, the default rating will be assumed.
    """

    query = (
        select(GameRequest).filter_by(
            variant=game_settings.variant,
            time_control=game_settings.time_control,
            increment=game_settings.increment,
            recipient=None,
        )
        # this makes sure guests can only play against guests
        # and authed users can only play against authed users
        .join(
            User,
            (GameRequest.inviter_id == User.user_id)
            & (User.user_type == user_type),
        )
    )

    if rating:
        # If a rating is provided, filter out game requests that are not in the valid range
        query = query.join(
            Rating,
            Rating.user_id == GameRequest.inviter_id,
            isouter=True,
        ).filter(
            func.coalesce(Rating.elo, literal(CONFIG.default_rating)).between(
                rating - CONFIG.acceptable_rating_difference,
                rating + CONFIG.acceptable_rating_difference,
            )
        )

    game_request = db.execute(query).scalar()
    return game_request
