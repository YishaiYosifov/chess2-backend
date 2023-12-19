from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.games.game_request_model import GameRequest
from app.models.rating_model import Rating
from app.models.user_model import AuthedUser
from app.constants import constants
from app.schemas import game_schema


# TODO: write test auhhh
def create_game_request(
    db: Session,
    user: AuthedUser,
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
):
    """
    Search for a game without a specified recipient that fits these conditions:
        - same settings (variant, time control and increment)
        - the inviter's rating is in the acceptable rating difference from the provided rating.
          If the inviter doesn't have a rating, the default rating will be assumed.
    """

    query = select(GameRequest).filter_by(
        variant=game_settings.variant,
        time_control=game_settings.time_control,
        increment=game_settings.increment,
        recipient=None,
    )

    if rating:
        # If a rating is provided, filter out game requests that are not in the valid range
        query = query.join(
            Rating, Rating.user_id == GameRequest.inviter_id, isouter=True
        ).filter(
            func.coalesce(Rating.elo, constants.DEFAULT_RATING).between(
                rating - constants.ACCEPTABLE_RATING_DIFFERENCE,
                rating + constants.ACCEPTABLE_RATING_DIFFERENCE,
            )
        )

    game = db.execute(query).scalar()
    return game
