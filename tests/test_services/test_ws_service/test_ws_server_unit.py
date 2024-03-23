import json

from pytest_mock.plugin import AsyncMockType
from pytest_mock import MockerFixture
from fastapi import WebSocketException, WebSocket
import redis.asyncio as aioredis
import pytest

from app.services.ws_service.ws_server import WSServer
from app.services.ws_service.ws_router import WSRouter
from tests.utils import dep_overrider
from app.main import app
from app import enums, deps

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_websocket(mocker: MockerFixture):
    return mocker.AsyncMock(spec=WebSocket)


@pytest.fixture
def mock_redis(mocker: MockerFixture):
    return mocker.AsyncMock(spec=aioredis.Redis)


@pytest.fixture
def test_ws_server(mock_redis):
    server = WSServer(redis_client=mock_redis)

    with dep_overrider.DependencyOverrider(
        app,
        {deps.get_ws_server: lambda: server},
    ):
        yield server


async def test_connect_websocket(
    mocker: MockerFixture,
    test_ws_server: WSServer,
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


async def test_emit(
    mocker: MockerFixture,
    test_ws_server: WSServer,
    mock_redis: AsyncMockType,
):
    """Test the message is publish correctly when emitting"""

    publish_mock = mocker.AsyncMock()
    mock_redis.publish = publish_mock

    event = enums.WSEvent.NOTIFICATION
    data = {"test": "ing"}
    to = 1
    await test_ws_server.emit(event, data, to)

    publish_mock.assert_called_once_with(
        test_ws_server._pubsub_channel, f"{to}:{event.value}:{json.dumps(data)}"
    )


def test_include_router(test_ws_server: WSServer):
    """Test routers are correctly added into the event handlers"""

    ws_router = WSRouter()

    @ws_router.on_event(enums.WSEvent.NOTIFICATION)
    def test_event_handler(ws_server: WSServer, data: dict):
        pass

    test_ws_server.include_router(ws_router)
    assert test_ws_server._event_handlers == ws_router._event_handlers


class TestHandleMessage:
    @pytest.mark.parametrize(
        "message",
        [
            "test",
            'invalid_event:{"key": "value"}',
            enums.WSEvent.GAME_START.value + ":invalid_json",
        ],
        ids=[
            "no event and json",
            "invalid event",
            "invalid json",
        ],
    )
    async def test_invalid_protocol(
        self,
        test_ws_server: WSServer,
        message: str,
    ):
        """Test an error is raised when the message protocol is invalid"""

        event = enums.WSEvent.GAME_START
        test_ws_server.on_event(event)(lambda a, b: ...)

        with pytest.raises(WebSocketException) as err:
            await test_ws_server._handle_message(message)
        assert err.value.code == 1002

    async def test_parses_json(
        self,
        mocker: MockerFixture,
        test_ws_server: WSServer,
    ):
        """Test the message is parsed and handled correctly"""

        event_handler = mocker.Mock()
        event = enums.WSEvent.GAME_START
        test_ws_server.on_event(event)(event_handler)
        message = {"key": "value"}

        await test_ws_server._handle_message(
            f"{event.value}:{json.dumps(message)}"
        )

        event_handler.assert_called_once_with(test_ws_server, message)

    async def test_correct_event_handler_ran(
        self, mocker: MockerFixture, test_ws_server: WSServer
    ):
        """Make sure only the correct event handler is ran"""

        correct_event_handler = mocker.Mock()
        wrong_event_handler = mocker.Mock()
        event = enums.WSEvent.GAME_START

        test_ws_server.on_event(enums.WSEvent.GAME_START)(correct_event_handler)
        test_ws_server.on_event(enums.WSEvent.NOTIFICATION)(wrong_event_handler)

        await test_ws_server._handle_message(
            f"{event.value}:{json.dumps({'key': 'value'})}"
        )

        correct_event_handler.assert_called_once()
        wrong_event_handler.assert_not_called()
