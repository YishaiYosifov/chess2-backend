from unittest.mock import patch
from glob import glob
import shutil

from fastapi.testclient import TestClient
from _pytest.fixtures import SubRequest
from sqlalchemy.orm import Session
import pytest

from app.dependencies import get_db
from tests.utils import mock_hash
from app.main import app
from app.db import engine


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
def mock_verify_password(request: SubRequest):
    with patch(
        "app.crud.user_crud.verify_password",
        lambda *args, **kwargs: request.param,
    ):
        yield
