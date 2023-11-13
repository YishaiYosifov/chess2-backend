from unittest.mock import _patch, patch

from fastapi import FastAPI

from app.models.games.game_model import Game
from app.models.user_model import User
from app.dependencies import authed_user_refresh, authed_user
from app.constants import enums
from app.crud import user_crud

from .dep_overrider import DependencyOverrider


def mock_hash() -> _patch:
    return patch.object(
        user_crud,
        "hash_password",
        return_value="$2b$12$kXC0QfbIfmjauYXOp9Hoj.ehDU1mWXgvTCvxlTVfEKyf35lR71Fam",
    )


def mock_login(app: FastAPI, user: User) -> DependencyOverrider:
    """
    Creates a context where the user is logged in.
    This is faster than sending a request to /auth/login because it doesn't actually generate a hash.

    :param user: a user object to mock login into
    """

    override = lambda: user
    override_authed_user = DependencyOverrider(
        app,
        overrides={
            authed_user: override,
            authed_user_refresh: override,
        },
    )
    return override_authed_user


def is_user_in_game(user: User, game: Game) -> bool:
    return (
        user.user_id == game.player_white.user_id
        if user.last_color == enums.Colors.WHITE
        else user.user_id == game.player_black.user_id
    )
