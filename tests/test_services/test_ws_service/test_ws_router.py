import itertools

import pytest

from app.services.ws_service.ws_server import WSServer
from app.services.ws_service.ws_router import WSRouter
from app import enums

pytestmark = pytest.mark.unit


@pytest.fixture
def ws_router():
    return WSRouter()


def test_on_event(ws_router: WSRouter):
    """Test functions are added to the router when registered"""

    @ws_router.on_event(enums.WSEventIn.MOVE)
    def test_event_handler(ws_server: WSServer, data: dict):
        pass

    assert ws_router._event_handlers == {
        enums.WSEventIn.MOVE: test_event_handler
    }


def test_iter(ws_router: WSRouter):
    """Test the iter functions returns the events correctly"""

    test_event_handlers = {
        enums.WSEventIn.MOVE: lambda ws_server, data: ...,
        enums.WSEventIn.RESIGN: lambda ws_server, data: ...,
    }
    ws_router._event_handlers = test_event_handlers

    assert all(
        a == b
        for a, b in itertools.zip_longest(
            ws_router, test_event_handlers.items()
        )
    )
