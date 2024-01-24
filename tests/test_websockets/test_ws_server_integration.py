from typing import AsyncContextManager

from httpx_ws import AsyncWebSocketSession
import redis.asyncio as aioredis
import pytest

from tests.factories.user import AuthedUserFactory
from app.websockets import ws_server
from tests.utils import dep_overrider, mocks
from app.main import app
from app import deps

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


@pytest.mark.usefixtures("db")
@pytest.mark.anyio
async def test_user_id_emits(
    async_ws_client: AsyncContextManager[AsyncWebSocketSession],
    test_ws_server: ws_server.WSServer,
):
    message = {"test": "message"}
    user = AuthedUserFactory.create()

    with mocks.mock_login(user):
        async with async_ws_client as ws:
            await test_ws_server.emit(message, user.user_id)
            assert await ws.receive_json() == message
