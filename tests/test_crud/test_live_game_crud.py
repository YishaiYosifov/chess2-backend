from sqlalchemy.orm import Session
import pytest

from tests.factories.game import LiveGameFactory
from app.crud import live_game_crud

{"pieces": [["piece", 0, 0], ["piece", 0, 0], ["piece", 0, 0]]}

pytestmark = pytest.mark.integration


def test_fetch_live_game_correct_token(db: Session):
    game = LiveGameFactory.create()
    fetched_game = live_game_crud.fetch_live_game(db, game.token)
    assert game == fetched_game


def test_fetch_live_game_incorrect_token(db: Session):
    LiveGameFactory.create()
    fetched_game = live_game_crud.fetch_live_game(db, "test token")
    assert not fetched_game
