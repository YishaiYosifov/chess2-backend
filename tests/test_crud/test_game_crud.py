from typing import NamedTuple

from _pytest.fixtures import SubRequest
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from sqlalchemy import select
import pytest

from app.models.games.live_player_model import LivePlayer
from app.models.games.game_result_model import GameResult
from app.models.user_model import AuthedUser
from tests.factories.user import (
    AuthedUserFactory,
    GuestUserFactory,
    PlayerFactory,
)
from tests.factories.game import GameResultFactory, LiveGameFactory
from app.crud import game_crud
from app import enums

pytestmark = pytest.mark.integration


class GameHistory(NamedTuple):
    user1: AuthedUser
    user2: AuthedUser
    games: list[GameResult]


@pytest.fixture
def game_history(db: Session, request: SubRequest) -> GameHistory:
    num_of_games: int = request.param

    user1 = AuthedUserFactory.create()
    user2 = AuthedUserFactory.create()
    games = GameResultFactory.create_history_batch(
        num_of_games,
        user1=user1,
        user2=user2,
    )

    return GameHistory(user1=user1, user2=user2, games=games)


@pytest.mark.parametrize("game_history", (0, 3), indirect=["game_history"])
def test_total(db: Session, game_history: GameHistory):
    assert game_crud.total_count(db, game_history.user1) == len(
        game_history.games
    )


@pytest.mark.parametrize(
    "page, per_page, game_history",
    [(0, 2, 3), (1, 2, 5), (0, 2, 1), (0, 2, 0)],
    indirect=["game_history"],
)
def test_paginate_history(
    db: Session,
    page: int,
    per_page: int,
    game_history: GameHistory,
):
    """
    Test the `paginate_history` crud function with
    different page and per_page values and different game history sizes
    """

    fetched_history = game_crud.paginate_history(
        db,
        game_history.user1,
        page=page,
        per_page=per_page,
    )
    expected_games = game_history.games[
        per_page * page : per_page * page + per_page
    ]

    assert len(fetched_history) == len(expected_games)
    assert all(
        existing_game.game_result_id == fetched_game.game_result_id
        for existing_game, fetched_game in zip(
            expected_games,
            fetched_history,
        )
    ), len(game_history.games)


@pytest.mark.parametrize(
    "random_color_results, expected_inviter_color, expected_recipient_color",
    [
        (enums.Color.WHITE, enums.Color.WHITE, enums.Color.BLACK),
        (enums.Color.BLACK, enums.Color.BLACK, enums.Color.WHITE),
    ],
)
@pytest.mark.parametrize("user_factory", [AuthedUserFactory, GuestUserFactory])
def test_create_players(
    db: Session,
    mocker: MockerFixture,
    random_color_results: enums.Color,
    expected_inviter_color: enums.Color,
    expected_recipient_color: enums.Color,
    user_factory: SQLAlchemyModelFactory,
):
    """
    Test the `create_players` crud function to ensure it correctly assigns the colors
    the to inviter and recipient, as well as how much time they have remaining.
    """

    mocker.patch.object(
        game_crud.random,
        "choice",
        return_value=random_color_results,
    )

    inviter = user_factory.create()
    recipient = user_factory.create()
    time_control = 69

    inviter_player, recipient_player = game_crud.create_players(
        db, inviter, recipient, time_control=time_control
    )

    assert len(db.execute(select(LivePlayer)).all()) == 2
    assert (
        inviter_player.time_remaining
        == recipient_player.time_remaining
        == time_control
    )

    assert inviter_player.user == inviter
    assert recipient_player.user == recipient

    assert inviter_player.color == expected_inviter_color
    assert recipient_player.color == expected_recipient_color


def test_create_game(db: Session, mocker: MockerFixture):
    """
    Test if the `create_game` crud function correctly assigns the players to the correct color,
    the correct game settings and correct creates a token
    """

    uuid_hex = "test-uuid"
    fen = "test-fen"
    mocker.patch.object(
        game_crud.uuid, "uuid4", return_value=mocker.Mock(hex=uuid_hex)
    )

    player_white = PlayerFactory.create(color=enums.Color.WHITE)
    player_black = PlayerFactory.create(color=enums.Color.BLACK)
    variant = enums.Variant.ANARCHY
    time_control = 420
    increment = 69

    game = game_crud.create_game(
        db,
        player_white,
        player_black,
        variant=variant,
        time_control=time_control,
        increment=increment,
        fen=fen,
    )

    # assert db.execute(select(Game)).scalar_one() == game
    assert game.variant == variant
    assert game.time_control == time_control
    assert game.increment == increment
    assert game.player_white == player_white
    assert game.player_black == player_black
    assert game.token == uuid_hex[:8]
    assert game.fen == fen


class TestFetchLiveGame:
    def test_correct_token(self, db: Session):
        """Try to fetch a live game with the correct token"""

        game = LiveGameFactory.create()
        fetched_game = game_crud.fetch_live_game(db, game.token)
        assert game == fetched_game

    def test_incorrect_token(self, db: Session):
        """Try to fetch a live game with a token that does not exist"""

        LiveGameFactory.create()
        fetched_game = game_crud.fetch_live_game(db, "test token")
        assert not fetched_game
