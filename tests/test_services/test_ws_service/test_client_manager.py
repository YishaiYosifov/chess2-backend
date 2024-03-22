from pytest_mock.plugin import MockType
from pytest_mock import MockerFixture
import pytest

from app.services.ws_service.client_manager import WebsocketClientManager


@pytest.fixture
def client_manager():
    return WebsocketClientManager()


@pytest.fixture
def ws_client(mocker: MockerFixture):
    return mocker.Mock()


@pytest.mark.unit
def test_get_clients_from_user(
    client_manager: WebsocketClientManager,
    ws_client: MockType,
):
    """Test getting client from a user id"""

    client_manager._clients = {1: ws_client}

    assert list(client_manager.get_clients(1)) == [ws_client]
    assert list(client_manager.get_clients(str(1))) == [ws_client]


@pytest.mark.unit
def test_get_clients_from_room(
    client_manager: WebsocketClientManager,
    ws_client: MockType,
):
    """Test getting clients from a room"""

    client_manager._clients = {1: ws_client}
    client_manager._rooms = {"test_room": {1}}

    assert list(client_manager.get_clients("test_room")) == [ws_client]


@pytest.mark.unit
def test_enter_room(client_manager: WebsocketClientManager):
    """
    Test if a new room is created when it doesn't exist
    and if the user id is added to the room if the room does exist
    """

    room_name = "test_room"
    user_id1, user_id2 = 1, 2

    client_manager.enter_room(room_name, user_id1)

    assert room_name in client_manager._rooms
    assert client_manager._rooms[room_name] == {user_id1}

    client_manager.enter_room(room_name, user_id2)
    assert client_manager._rooms[room_name] == {user_id1, user_id2}


@pytest.mark.unit
def test_leave_room(client_manager: WebsocketClientManager):
    client_manager._rooms = {"test_room": {1}}
    client_manager.leave_room("test_room", 1)

    assert not client_manager._rooms


@pytest.mark.unit
def test_close_room(client_manager: WebsocketClientManager):
    client_manager._rooms = {"test_room": {1}}
    client_manager.close_room("test_room")

    assert not client_manager._rooms


@pytest.mark.unit
def test_add_client(
    client_manager: WebsocketClientManager,
    ws_client: MockType,
):
    client_manager.add_client(1, ws_client)
    assert client_manager._clients[1] == ws_client


@pytest.mark.unit
def test_remove_client(
    client_manager: WebsocketClientManager,
    ws_client: MockType,
):
    client_manager._clients = {1: ws_client}
    client_manager.remove_client(1)
    assert not client_manager._clients.get(1)
