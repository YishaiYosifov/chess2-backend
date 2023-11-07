from glob import glob
import shutil

from fastapi.testclient import TestClient
from pytest_factoryboy import register
from sqlalchemy.orm import Session
import pytest

from tests.factories.user import RuntimePlayerInfoFactory, UserFactory
from tests.factories.game import GameRequestFactory, GameFactory
from app.dependencies import get_db
from tests.utils import mock_hash
from app.main import app
from app.db import engine

# region Pytest Factoryboy

# Create fixtures for each factory which uses the db fixture.
# This is necessary because this is the ony way for the factories to use the db fixture.


@pytest.fixture
def user_factory(db: Session):
    return UserFactory


@pytest.fixture
def runtime_player_info_factory(db: Session):
    return RuntimePlayerInfoFactory


@pytest.fixture
def game_factory(db: Session):
    return GameFactory


@pytest.fixture
def game_request_factory(db: Session):
    return GameRequestFactory


register(UserFactory)
register(RuntimePlayerInfoFactory)

register(GameFactory)
register(GameRequestFactory)

# endregion


@pytest.fixture(scope="session")
def client():
    yield TestClient(app)
    for file in glob("uploads/*"):
        shutil.rmtree(file)


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()

    # bind an individual Session to the connection
    session = Session(bind=connection)
    app.dependency_overrides[get_db] = lambda: session

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="mock_hash")
def fix_mock_hash():
    with mock_hash():
        yield


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
