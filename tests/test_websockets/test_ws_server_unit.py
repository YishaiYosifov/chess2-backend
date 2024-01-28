import json

from pytest_mock.plugin import AsyncMockType
from pytest_mock import MockerFixture
from fastapi import WebSocket
import redis.asyncio as aioredis
import pytest

from tests.utils.test_common import AsyncIterator
from app.websockets import ws_server
from app.constants import enums
from tests.utils import dep_overrider
from app.main import app
from app import deps

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_websocket(mocker: MockerFixture):
    return mocker.AsyncMock(spec=WebSocket)


@pytest.fixture
def mock_redis(mocker: MockerFixture):
    return mocker.AsyncMock(spec=aioredis.Redis)


@pytest.fixture
def test_ws_server(mock_redis):
    server = ws_server.WSServer(redis_client=mock_redis)

    with dep_overrider.DependencyOverrider(
        app,
        {deps.get_ws_server: lambda: server},
    ):
        yield server


async def test_connect_websocket(
    mocker: MockerFixture,
    test_ws_server: ws_server.WSServer,
    mock_websocket: AsyncMockType,
):
    """Test the websocket client is added and removed correctly"""

    user_id = 1
    add_client_mock = mocker.Mock()
    remove_client_mock = mocker.Mock()

    test_ws_server.clients.add_client = add_client_mock
    test_ws_server.clients.remove_client = remove_client_mock

    await test_ws_server.connect_websocket(mock_websocket, user_id)

    add_client_mock.assert_called_once_with(user_id, mock_websocket)
    remove_client_mock.assert_called_once_with(user_id)


async def test_forwards_on_receive(
    mocker: MockerFixture,
    test_ws_server: ws_server.WSServer,
    mock_websocket: AsyncMockType,
):
    """Test the `on_receive` function is called when messages are received"""

    messages = ["1", 2, "test"]

    mock_websocket.iter_text.return_value = AsyncIterator(messages)
    on_receive = mocker.Mock()

    await test_ws_server.connect_websocket(mock_websocket, 1, on_receive)

    on_receive.assert_has_calls([mocker.call(message) for message in messages])  # type: ignore


async def test_emit(
    mocker: MockerFixture,
    test_ws_server: ws_server.WSServer,
    mock_redis: AsyncMockType,
):
    """Test the message is publish correctly when emitting"""

    publish_mock = mocker.AsyncMock()
    mock_redis.publish = publish_mock

    event = enums.WebsocketEvent.NOTIFICATION
    data = {"test": "ing"}
    to = 1
    await test_ws_server.emit(event, data, to)

    publish_mock.assert_called_once_with(
        test_ws_server._pubsub_channel, f"{to}:{event.value}:{json.dumps(data)}"
    )
