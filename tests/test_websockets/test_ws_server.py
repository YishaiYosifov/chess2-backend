from fastapi.testclient import TestClient
import redis.asyncio as aioredis
import pytest

from tests.factories.user import AuthedUserFactory
from app.websockets import ws_server
from tests.utils import dep_overrider, mocks
from app.main import app
from app import deps


@pytest.fixture
async def test_ws_server(redis: aioredis.Redis):
    server = ws_server.WSServer(redis)
    server.connect_pubsub()

    with dep_overrider.DependencyOverrider(
        app,
        {deps.get_ws_server: lambda: server},
    ):
        yield server

    await server.disconnect_pubsub()


@pytest.mark.integration
@pytest.mark.usefixtures("db")
async def test_ws_connect(
    client: TestClient, test_ws_server: ws_server.WSServer
):
    user = AuthedUserFactory.create()
    with mocks.mock_login(user), client.websocket_connect("/ws"):
        assert user.user_id in getattr(test_ws_server.clients, "_clients")
