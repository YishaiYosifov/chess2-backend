import os

from app.websockets import ws_server

os.environ["ENV"] = ".env.test.local"

from glob import glob
import shutil

from fastapi.testclient import TestClient
from _pytest.fixtures import SubRequest
from sqlalchemy.orm import scoped_session, sessionmaker
from pytest_mock import MockerFixture
from httpx import AsyncClient
import pytest

from app.schemas.config_schema import get_config
from tests.utils.db_mock import DbMock
from app.services import auth_service, jwt_service
from app.main import app
from app.deps import get_db
from app.db import engine

TestScopedSession = scoped_session(sessionmaker())


@pytest.fixture(scope="session")
def client():
    yield TestClient(app)

    for file in glob("uploads/*"):
        shutil.rmtree(file)


@pytest.fixture(scope="session", autouse=True)
async def initialize_websockets(anyio_backend):
    ws_server.initilize()


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
def mock_password_hash(request: SubRequest, mocker: MockerFixture) -> str:
    new_hash = getattr(
        request,
        "param",
        "$2b$12$kXC0QfbIfmjauYXOp9Hoj.ehDU1mWXgvTCvxlTVfEKyf35lR71Fam",
    )
    mocker.patch.object(
        auth_service,
        "hash_password",
        return_value=new_hash,
    )

    return new_hash


@pytest.fixture
def mock_create_jwt_tokens(request: SubRequest, mocker: MockerFixture) -> str:
    new_token = getattr(request, "param", "new token")

    mocker.patch.object(
        jwt_service,
        "create_access_token",
        return_value=new_token,
    )
    mocker.patch.object(
        jwt_service,
        "create_refresh_token",
        return_value=new_token,
    )

    return new_token


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def config():
    return get_config()


@pytest.fixture
def db_mock():
    return DbMock()
