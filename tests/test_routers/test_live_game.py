from http import HTTPStatus

from httpx import AsyncClient
import pytest

from app.models.games.live_player_model import LivePlayer
from app.models.games.game_piece_model import GamePiece
from tests.factories.game import LiveGameFactory


@pytest.mark.usefixtures("db")
class TestLoadGame:
    def _assert_pieces(
        self,
        pieces: list[GamePiece],
        fetched_pieces: list[dict],
    ) -> None:
        """
        Assert the existing pieces and the fetched pieces are equal

        :param pieces: the existing game pieces
        :param fetched_pieces: the pieces fetched from the endpoint
        """

        for existing_piece, fetched_piece in zip(pieces, fetched_pieces):
            assert (
                existing_piece.piece_type.value == fetched_piece["piece_type"]
            )
            assert existing_piece.color.value == fetched_piece["color"]
            assert existing_piece.x == fetched_piece["x"]
            assert existing_piece.y == fetched_piece["y"]

    def _assert_player(self, player: LivePlayer, fetched_player: dict) -> None:
        """
        Assert a player and the fetched player are equal

        :param player: the existing player
        :param fetched_player: the player fetched from the endpoint
        """

        assert player.user.user_id == fetched_player["user"]["user_id"]
        assert player.color.value == fetched_player["color"]
        assert player.time_remaining == fetched_player["time_remaining"]

    async def test_game_exists(self, async_client: AsyncClient):
        """Test that the game is fetched correctly with all the neccasary data"""

        game = LiveGameFactory.create()
        async with async_client as ac:
            response = await ac.get(f"/live-game/{game.token}/load")

        assert response.status_code == HTTPStatus.OK

        data = response.json()

        assert "pieces" in data
        self._assert_pieces(game.pieces, data["pieces"])

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
