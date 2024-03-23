import os

os.environ["ENV"] = "test.env"

from glob import glob
import inspect
import shutil

from httpx_ws.transport import ASGIWebSocketTransport
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from httpx import AsyncClient
import redis.asyncio as aioredis
import httpx_ws
import pytest
import httpx

from app.schemas.config_schema import get_config, CONFIG
from tests.utils.test_common import TestScopedSession
from app.services.ws_service import ws_server_inst
from tests.factories.user import AuthedUserFactory
from tests.utils import mocks
from app.main import app
from app.deps import get_db
from app.db import engine


@pytest.fixture(scope="session")
def client(connect_websockets):
    yield TestClient(app)

    for file in glob("uploads/*"):
        shutil.rmtree(file)


@pytest.fixture
def async_client(connect_websockets):
    return AsyncClient(app=app, base_url="http://testserver")


@pytest.fixture(scope="session")
async def connect_websockets(anyio_backend):
    await ws_server_inst.connect_pubsub()
    yield
    await ws_server_inst.disconnect_pubsub()


@pytest.fixture
def async_ws_client():
    client = httpx.AsyncClient(transport=ASGIWebSocketTransport(app))
    return httpx_ws.aconnect_ws("ws://testserver/ws", client)


@pytest.fixture
def db():
    # bind an individual Session to the connection
    connection = engine.connect()
    transaction = connection.begin()

    session = TestScopedSession(bind=connection)
    app.dependency_overrides[get_db] = lambda: session

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    TestScopedSession.remove()


@pytest.fixture
async def redis(anyio_backend):
    redis_client = aioredis.from_url(CONFIG.redis_url)
    yield redis_client
    await redis_client.flushall(True)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def config():
    return get_config()


@pytest.hookimpl(tryfirst=True)
def pytest_pycollect_makeitem(collector, name, obj) -> None:
    """Automatically mark async tests with anyio"""

    if not collector.istestfunction(obj, name):
        return

    if inspect.iscoroutinefunction(obj):
        pytest.mark.usefixtures("anyio_backend")(obj)


@pytest.fixture
def authed_user(db: Session):
    user = AuthedUserFactory.create()
    with mocks.mock_login(user):
        yield user
