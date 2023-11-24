import os

os.environ["ENV"] = ".env.test.local"

from glob import glob
import shutil

from fastapi.testclient import TestClient
from sqlalchemy.orm import scoped_session, sessionmaker
import pytest

from app.schemas.config_schema import get_settings
from tests.utils import mocks
from app.main import app
from app.deps import get_db
from app.db import engine

TestScopedSession = scoped_session(sessionmaker())


@pytest.fixture(scope="session")
def client():
    client = TestClient(app)
    yield client

    for file in glob("uploads/*"):
        shutil.rmtree(file)


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


@pytest.fixture(name="mock_hash")
def fix_mock_hash():
    with mocks.mock_hash():
        yield


@pytest.fixture(scope="session")
def settings():
    return get_settings()
