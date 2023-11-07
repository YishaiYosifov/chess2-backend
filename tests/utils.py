from unittest.mock import _patch, patch

from app.models.games.game import Game
from app.constants.enums import Colors
from app.models.user import User
from app.crud import user_crud


def mock_hash() -> _patch:
    return patch.object(
        user_crud,
        "hash_password",
        return_value="$2b$12$kXC0QfbIfmjauYXOp9Hoj.ehDU1mWXgvTCvxlTVfEKyf35lR71Fam",
    )


def mock_login() -> _patch:
    """
    Creates a context where the user is logged in.
    This is faster than sending a request to /api/auth/login because it doesn't actually generate a hash.

    :param user: a user object or a user id
    """

    patch_jwt_in_request = patch.object(
        user_crud,
        "verify_password",
        return_value=True,
    )
    return patch_jwt_in_request


def is_user_in_game(user: User, game: Game) -> bool:
    return (
        user.user_id == game.player_white.user_id
        if user.last_color == Colors.WHITE
        else user.user_id == game.player_black.user_id
    )
