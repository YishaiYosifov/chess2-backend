from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy import select
from httpx import AsyncClient
import pytest

from app.models.games.game_request_model import GameRequest
from app.models.games.game_model import Game
from app.models.user_model import User
from tests.factories.user import (
    AuthedUserFactory,
    GuestUserFactory,
    PlayerFactory,
)
from tests.factories.game import (
    GameSettingsFactory,
    GameRequestFactory,
    GameFactory,
)
from app.constants import enums
from tests.utils import mocks


@pytest.mark.anyio
@pytest.mark.integration
@pytest.mark.usefixtures("db")
class TestStartPoolGame:
    async def join_pool(
        self,
        async_client: AsyncClient,
        user: User,
        game_settings=GameSettingsFactory.build(),
    ):
        with mocks.mock_login(user):
            async with async_client as ac:
                return await ac.post(
                    "/game-requests/pool/join",
                    json={
                        "variant": game_settings.variant.value,
                        "time_control": game_settings.time_control,
                        "increment": game_settings.increment,
                    },
                )

    async def test_fail_with_active_game(self, async_client: AsyncClient):
        """Test that you cannot start a game if you're already in a game"""

        user = AuthedUserFactory.create()
        GameFactory.create(
            player_white=PlayerFactory.create(user=user), player_black=None
        )

        response = await self.join_pool(async_client, user)
        assert response.status_code == HTTPStatus.CONFLICT

    async def test_no_existing_request_found(
        self, db: Session, async_client: AsyncClient
    ):
        """Test if a game request is created if there is no existing request"""

        user = AuthedUserFactory.create()
        response = await self.join_pool(async_client, user)

        assert response.status_code == HTTPStatus.CREATED
        assert db.execute(select(GameRequest)).scalar_one().inviter == user

    async def test_existing_request_found(
        self, db: Session, async_client: AsyncClient
    ):
        """Test that a game is started if there is an existing request"""

        user = AuthedUserFactory.create()
        GameRequestFactory.create()

        response = await self.join_pool(async_client, user)
        assert response.status_code == HTTPStatus.OK
        assert db.execute(select(Game)).scalar_one()

    async def test_user_has_request(
        self, db: Session, async_client: AsyncClient
    ):
        """Test that if the user already has a game request it is deleted"""

        user = AuthedUserFactory.create()
        GameRequestFactory.create(inviter=user)
        db.flush()

        response = await self.join_pool(async_client, user)
        assert response.status_code == HTTPStatus.CREATED
        assert db.execute(select(GameRequest)).scalar_one()

    @pytest.mark.parametrize(
        "user_type", [enums.UserType.AUTHED, enums.UserType.GUEST]
    )
    async def test_request_found_wrong_user_type(
        self, async_client: AsyncClient, user_type: enums.UserType
    ):
        """Test that a guest user can't match with an authed user"""

        if user_type == enums.UserType.GUEST:
            GameRequestFactory.create(inviter=AuthedUserFactory.create())
            user = GuestUserFactory.create()
        else:
            GameRequestFactory.create(inviter=GuestUserFactory.create())
            user = AuthedUserFactory.create()

        response = await self.join_pool(async_client, user)
        assert response.status_code == HTTPStatus.CREATED
