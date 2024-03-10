from typing import AsyncContextManager
import json

from httpx_ws import AsyncWebSocketSession
import redis.asyncio as aioredis
import pytest

from tests.factories.user import AuthedUserFactory
from app.websockets import ws_server
from tests.utils import dep_overrider, mocks
from app.main import app
from app import enums, deps

pytestmark = pytest.mark.integration


@pytest.fixture
async def test_ws_server(redis: aioredis.Redis):
    server = ws_server.WSServer(redis)
    await server.connect_pubsub()

    with dep_overrider.DependencyOverrider(
        app,
        {deps.get_ws_server: lambda: server},
    ):
        yield server

    await server.disconnect_pubsub()


@pytest.mark.usefixtures("db")
async def test_ws_connect(
    async_ws_client: AsyncContextManager[AsyncWebSocketSession],
    test_ws_server: ws_server.WSServer,
):
    user = AuthedUserFactory.create()
    with mocks.mock_login(user):
        async with async_ws_client as ws:
            assert user.user_id in getattr(test_ws_server.clients, "_clients")
            await ws.close()


class TestEmit:
    event = enums.WSEvent.NOTIFICATION
    data = {"test": "message"}
    expected_message = f"{event.value}:{json.dumps(data)}"

    @pytest.mark.usefixtures("db")
    async def test_user_id_emits(
        self,
        async_ws_client: AsyncContextManager[AsyncWebSocketSession],
        test_ws_server: ws_server.WSServer,
    ):
        """Test emits to a specific user"""

        user = AuthedUserFactory.create()

        with mocks.mock_login(user):
            async with async_ws_client as ws:
                await test_ws_server.emit(self.event, self.data, user.user_id)
                assert await ws.receive_text(3) == self.expected_message

    @pytest.mark.usefixtures("db")
    async def test_room_emits(
        self,
        async_ws_client: AsyncContextManager[AsyncWebSocketSession],
        test_ws_server: ws_server.WSServer,
    ):
        """Test emits to a room"""

        room = "test room"
        user = AuthedUserFactory.create()

        with mocks.mock_login(user):
            async with async_ws_client as ws:
                test_ws_server.clients.enter_room(room, user.user_id)
                await test_ws_server.emit(self.event, self.data, room)

                assert await ws.receive_text(3) == self.expected_message
