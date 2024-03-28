from typing import AsyncContextManager
import json

from httpx_ws import AsyncWebSocketSession
import redis.asyncio as aioredis
import pytest

from app.services.ws_service.ws_server import WSServer
from app.models.user_model import AuthedUser
from tests.utils import dep_overrider
from app.main import app
from app import enums, deps

pytestmark = pytest.mark.integration
AsyncWSClient = AsyncContextManager[AsyncWebSocketSession]


@pytest.fixture
async def test_ws_server(redis: aioredis.Redis):
    server = WSServer(redis)
    await server.connect_pubsub()

    with dep_overrider.DependencyOverrider(
        app,
        {deps.get_ws_server: lambda: server},
    ):
        yield server

    await server.disconnect_pubsub()


@pytest.mark.usefixtures("db")
async def test_ws_connect(
    authed_user: AuthedUser,
    async_ws_client: AsyncWSClient,
    test_ws_server: WSServer,
):
    async with async_ws_client as ws:
        assert authed_user.user_id in getattr(
            test_ws_server.clients,
            "_clients",
        )
        await ws.close()


class TestEmit:
    event = enums.WSEventOut.NOTIFICATION
    data = {"test": "message"}
    expected_message = f"{event.value}:{json.dumps(data)}"

    @pytest.mark.usefixtures("db")
    async def test_user_id_emits(
        self,
        authed_user: AuthedUser,
        async_ws_client: AsyncWSClient,
        test_ws_server: WSServer,
    ):
        """Test emits to a specific user"""

        async with async_ws_client as ws:
            await test_ws_server.emit(
                self.event,
                self.data,
                authed_user.user_id,
            )
            assert await ws.receive_text(3) == self.expected_message

    @pytest.mark.usefixtures("db")
    async def test_room_emits(
        self,
        authed_user: AuthedUser,
        async_ws_client: AsyncWSClient,
        test_ws_server: WSServer,
    ):
        """Test emits to a room"""

        room = "test room"

        async with async_ws_client as ws:
            test_ws_server.clients.enter_room(room, authed_user.user_id)
            await test_ws_server.emit(self.event, self.data, room)

            assert await ws.receive_text(3) == self.expected_message


async def test_on_receive(
    authed_user: AuthedUser,
    async_ws_client: AsyncWSClient,
    test_ws_server: WSServer,
):
    """Test the event handler is actually ran when a message is received"""

    event = enums.WSEventIn.MOVE
    message = {"key": "value"}

    @test_ws_server.on_event(event)
    async def _(ws_server: WSServer, data: dict):
        websocket = list(ws_server.clients.get_clients(authed_user.user_id))[0]
        await websocket.send_json(data)

    async with async_ws_client as ws:
        await ws.send_text(f"{event.value}:{json.dumps(message)}")
        assert await ws.receive_json(3) == message
