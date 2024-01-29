from typing import AsyncContextManager
from http import HTTPStatus
import json

from sqlalchemy.orm import Session
from sqlalchemy import select
from httpx_ws import AsyncWebSocketSession
from httpx import AsyncClient
import pytest

from app.models.games.game_request_model import GameRequest
from app.models.games.live_game_model import LiveGame
from app.models.user_model import User
from tests.factories.user import (
    AuthedUserFactory,
    GuestUserFactory,
    PlayerFactory,
)
from tests.factories.game import (
    GameSettingsFactory,
    GameRequestFactory,
    LiveGameFactory,
)
from app.constants import enums
from tests.utils import mocks


@pytest.mark.integration
@pytest.mark.usefixtures("db")
class TestJoinPoolGame:
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
        LiveGameFactory.create(
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
        self,
        async_ws_client: AsyncContextManager[AsyncWebSocketSession],
        db: Session,
        async_client: AsyncClient,
    ):
        """Test that a game is started if there is an existing request"""

        recipient = AuthedUserFactory.create()
        inviter = AuthedUserFactory.create()
        GameRequestFactory.create(inviter=inviter)

        with mocks.mock_login(inviter):
            async with async_ws_client as ws:
                response = await self.join_pool(async_client, recipient)
                ws_received = await ws.receive_text(3)

        assert response.status_code == HTTPStatus.OK

        created_game = db.execute(select(LiveGame)).scalar_one()
        assert created_game
        assert ws_received == (
            f"{enums.WebsocketEvent.GAME_START.value}:"
            f"{json.dumps(created_game.token)}"
        )

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
