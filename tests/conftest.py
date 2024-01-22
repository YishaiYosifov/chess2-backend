import os

os.environ["ENV"] = ".env.test.local"

from glob import glob
import inspect
import shutil

from fastapi.testclient import TestClient
from sqlalchemy.orm import scoped_session, sessionmaker
from httpx import AsyncClient
import pytest

from app.schemas.config_schema import get_config
from app.websockets import ws_server_instance
from app.main import app
from app.deps import get_db
from app.db import redis_client, engine

TestScopedSession = scoped_session(sessionmaker())


@pytest.fixture(scope="session")
def client():
    yield TestClient(app)

    for file in glob("uploads/*"):
        shutil.rmtree(file)


@pytest.fixture(scope="session", autouse=True)
async def connect_websockets(anyio_backend):
    ws_server_instance.connect_pubsub()
    yield
    await ws_server_instance.disconnect_pubsub()


@pytest.fixture
def async_client():
    return AsyncClient(app=app, base_url="http://testserver")


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
    yield redis_client
    await redis_client.flushall(True)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def config():
    return get_config()


def pytest_collection_modifyitems(items):
    """Automatically mark async tests with anyio"""

    for test in items:
        if inspect.iscoroutinefunction(test):
            test.add_market(pytest.mark.anyio)
