from typing import NamedTuple

from _pytest.fixtures import SubRequest
from sqlalchemy.orm import Session
import pytest

from app.models.games.game_results_model import GameResult
from app.models.user_model import User
from tests.factories.user import UserFactory
from tests.factories.game import GameResultFactory
from app.crud import game_crud


class GameHistory(NamedTuple):
    user1: User
    user2: User
    games: list[GameResult]


@pytest.fixture
def game_history(db, request: SubRequest) -> GameHistory:
    num_of_games: int = request.param

    user1 = UserFactory.create()
    user2 = UserFactory.create()
    games = GameResultFactory.create_history_batch(
        num_of_games,
        user1=user1,
        user2=user2,
    )

    return GameHistory(user1=user1, user2=user2, games=games)


@pytest.mark.parametrize("game_history", (0, 3), indirect=["game_history"])
def test_total(db: Session, game_history: GameHistory):
    """Test if the `page_count` crud function counts the required amount of pages correctly"""

    assert game_crud.total(db, game_history.user1) == len(game_history.games)


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
    """Test the `paginate_history` crud function with different senarios"""

    fetched_history = game_crud.paginate_history(
        db,
        game_history.user1,
        page=page,
        per_page=per_page,
    )
    expected_games = game_history.games[per_page * page : per_page * page + per_page]

    assert len(fetched_history) == len(expected_games)
    assert all(
        existing_game.game_results_id == fetched_game.game_results_id
        for existing_game, fetched_game in zip(
            expected_games,
            fetched_history,
        )
    ), len(game_history.games)
