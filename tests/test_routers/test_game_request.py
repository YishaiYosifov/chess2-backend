from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy import select
from httpx import AsyncClient
import pytest

from app.models.games.game_request_model import GameRequest
from app.models.games.game_model import Game
from app.models.user_model import AuthedUser
from tests.factories.user import AuthedUserFactory, PlayerFactory
from tests.factories.game import GameRequestFactory, GameFactory
from app.constants import enums
from tests.utils import mocks


@pytest.mark.integration
@pytest.mark.usefixtures("db")
class TestStartPoolGame:
    async def _send_request(
        self,
        async_client: AsyncClient,
        user: AuthedUser,
        variant: enums.Variant = enums.Variant.ANARCHY,
        time_control: int = 69,
        increment: int = 10,
    ):
        with mocks.mock_login(user):
            async with async_client as ac:
                return await ac.post(
                    "/game-requests/pool/join",
                    json={
                        "variant": variant.value,
                        "time_control": time_control,
                        "increment": increment,
                    },
                )

    async def test_fail_with_active_game(self, async_client: AsyncClient):
        """Test that you cannot start a game if you're already in a game"""

        user = AuthedUserFactory.create()
        GameFactory.create(
            player_white=PlayerFactory.create(user=user), player_black=None
        )

        response = await self._send_request(async_client, user)
        assert response.status_code == HTTPStatus.CONFLICT

    async def test_no_existing_request_found(
        self, async_client: AsyncClient, db: Session
    ):
        """Test if a game request is created if there is no existing request"""

        user = AuthedUserFactory.create()
        response = await self._send_request(async_client, user)

        assert response.status_code == HTTPStatus.CREATED
        assert db.execute(select(GameRequest)).scalar_one().inviter == user

    async def test_existing_request_found(
        self, async_client: AsyncClient, db: Session
    ):
        """Test that a game is started if there is an existing request"""

        user = AuthedUserFactory.create()

        variant = enums.Variant.ANARCHY
        time_control = 69
        increment = 10
        GameRequestFactory.create(
            variant=variant,
            time_control=time_control,
            increment=increment,
        )

        response = await self._send_request(
            async_client, user, variant, time_control, increment
        )
        assert response.status_code == HTTPStatus.OK
        assert db.execute(select(Game)).scalar_one()

    async def test_user_has_request(
        self, async_client: AsyncClient, db: Session
    ):
        """Test that if the user already has a game request it is deleted"""

        user = AuthedUserFactory.create()
        GameRequestFactory.create(inviter=user)
        db.flush()

        response = await self._send_request(async_client, user)
        assert response.status_code == HTTPStatus.CREATED
        assert db.execute(select(GameRequest)).scalar_one()
