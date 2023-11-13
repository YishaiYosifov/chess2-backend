import os

os.environ["ENV"] = ".env.test.local"

from glob import glob
import shutil

from fastapi.testclient import TestClient
from sqlalchemy.orm import scoped_session, sessionmaker
import pytest

from app.schemas.config_schema import get_settings
from tests.utils.common import mock_hash
from app.dependencies import get_db
from app.main import app
from app.db import engine

ScopedSession = scoped_session(sessionmaker())


@pytest.fixture(scope="session")
def client():
    yield TestClient(app)

    for file in glob("uploads/*"):
        shutil.rmtree(file)


@pytest.fixture
def db():
    # bind an individual Session to the connection
    connection = engine.connect()
    transaction = connection.begin()

    session = ScopedSession(bind=connection)
    app.dependency_overrides[get_db] = lambda: session

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    ScopedSession.remove()


@pytest.fixture(name="mock_hash")
def fix_mock_hash():
    with mock_hash():
        yield


@pytest.fixture(scope="session")
def settings():
    return get_settings()
