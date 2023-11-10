from unittest.mock import patch
from http import HTTPStatus

from fastapi.testclient import TestClient
from _pytest.fixtures import SubRequest
from sqlalchemy.orm import Session
import pytest

from tests.factories.user import UserFactory


@pytest.fixture
def mock_verify_password(request: SubRequest):
    with patch(
        "app.crud.user_crud.verify_password",
        lambda *args, **kwargs: request.param,
    ):
        yield


@pytest.mark.parametrize(
    "data, mock_verify_password",
    [
        [{"username": "non-existing-user", "password": "password"}, True],
        [{"username": "test-user", "password": "bad password"}, False],
    ],
    indirect=["mock_verify_password"],
)
@pytest.mark.usefixtures("mock_verify_password")
def test_login_fail(db: Session, client: TestClient, data):
    """Test how `/auth/login` handles non existing credentials"""

    UserFactory.create(session=db, username="test-user")
    response = client.post(
        "/auth/login",
        data=data,
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json()


@pytest.mark.parametrize("mock_verify_password", [True], indirect=True)
@pytest.mark.usefixtures("mock_verify_password")
def test_login_success(db: Session, client: TestClient):
    "Test how `/auth/login` handles valid credentials"

    user = UserFactory.create(session=db)
    response = client.post(
        "/auth/login",
        data={
            "username": user.username,
            "password": "password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == HTTPStatus.OK, response.json()

    response_json: dict | None = response.json()
    assert response_json

    assert "access_token" in response_json
    assert "refresh_token" in response_json