from sqlalchemy.orm import Session

from tests.factories.game import LiveGameFactory


class TestGet:
    async def test_game_exists(self, db: Session):
        game = LiveGameFactory.create()
