from http import HTTPStatus

from httpx import AsyncClient
import pytest

from app.models.games.live_player_model import LivePlayer
from app.schemas.config_schema import Config
from tests.factories.game import LiveGameFactory


@pytest.mark.usefixtures("db")
@pytest.mark.integration
class TestLoadGame:
    def _assert_player(self, player: LivePlayer, fetched_player: dict) -> None:
        """
        Assert a player and the fetched player are equal

        :param player: the existing player
        :param fetched_player: the player fetched from the endpoint
        """

        assert player.user.user_id == fetched_player["user"]["user_id"]
        assert player.color.value == fetched_player["color"]
        assert player.time_remaining == fetched_player["time_remaining"]

    async def test_game_exists(self, async_client: AsyncClient, config: Config):
        """Test that the game is fetched correctly with all the neccasary data"""

        game = LiveGameFactory.create()
        async with async_client as ac:
            response = await ac.get(f"/live-game/{game.token}/load")

        assert response.status_code == HTTPStatus.OK

        data = response.json()

        assert "fen" in data
        assert data["fen"] == config.default_fen

        assert "player_white" in data
        assert "player_black" in data

        self._assert_player(game.player_white, data["player_white"])
        self._assert_player(game.player_black, data["player_black"])

        assert "turn_player_id" in data

    async def test_game_doesnt_exist(self, async_client: AsyncClient):
        """Test that 404 is returned when the game is not found"""

        async with async_client as ac:
            response = await ac.get("/live-game/test-token/load")
        assert response.status_code == HTTPStatus.NOT_FOUND
