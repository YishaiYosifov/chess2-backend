from sqlalchemy.orm import Session

from app.models.games.game_request_model import GameRequest
from app.models.games.game_model import Game
from app.models.user_model import AuthedUser, User
from app.constants import enums
from app.schemas import game_schema
from app.crud import game_request_crud, rating_crud, game_crud


def start_game_request(
    db: Session,
    game_request: GameRequest,
    recipient: User | None = None,
) -> Game:
    """
    Create the game from the game request.
    This function creates the game and assigns the colors and sets the users last color.

    :param db: the database session
    :param game_request: the request to start
    :param recipient: only needs to be provided for games where the recipient was not already provided.
    :raises ValueError: recipient was not provided in the creation of the game request / to this method.
    """

    recipient = recipient or game_request.recipient
    if not recipient:
        raise ValueError("Recipient not provided")

    inviter_player, recipient_player = game_crud.create_players(
        db,
        game_request.inviter,
        recipient,
        game_request.time_control,
    )

    game = game_crud.create_game(
        db,
        inviter_player,
        recipient_player,
        game_request.variant,
        game_request.time_control,
        game_request.increment,
    )
    game_crud.create_pieces(db, game)

    db.delete(game_request)
    return game


def create_or_start_pool_game(
    db: Session,
    user: User,
    game_settings: game_schema.GameSettings,
) -> str | None:
    """
    Search for a game request with a matching rating and game options.
    If a game request was found, start the game.
    If not, create a new game request.

    :param db: the database session
    :param user: the user for whom to search a game request
    :param game_settings: the game settings object

    :return: the game token if a request was found, otherwise None
    """

    is_authed = isinstance(user, AuthedUser)
    rating = (
        rating_crud.fetch_rating_value(db, user, game_settings.variant)
        if is_authed
        else None
    )

    found_game_request = game_request_crud.search_game_request(
        db,
        game_settings,
        rating,
        enums.UserType.AUTHED if is_authed else enums.UserType.GUEST,
    )
    if found_game_request:
        game = start_game_request(db, found_game_request, user)
        return game.token

    game_request_crud.create_game_request(db, user, game_settings)
