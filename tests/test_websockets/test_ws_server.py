from fastapi.testclient import TestClient
import pytest


@pytest.mark.anyio
def test_handle(client: TestClient):
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("test")
