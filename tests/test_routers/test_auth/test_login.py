from unittest.mock import patch
from http import HTTPStatus

from fastapi.testclient import TestClient
from _pytest.fixtures import SubRequest
import pytest

from app.models.user_model import AuthedUser
from tests.factories.user import AuthedUserFactory
from app.crud import user_crud


@pytest.fixture
def mock_verify_password(request: SubRequest):
    with patch.object(user_crud, "auth_service") as a:
        a.verify_password.return_value = request.param
        yield


@pytest.mark.integration
@pytest.mark.parametrize(
    "data, mock_verify_password",
    (
        [{"username": "non-existing-user", "password": "password"}, True],
        [{"username": "test-user", "password": "bad password"}, False],
    ),
    indirect=["mock_verify_password"],
)
@pytest.mark.usefixtures("mock_verify_password", "db")
def test_login_fail(client: TestClient, data):
    """Test how `/auth/login` handles non existing credentials"""

    AuthedUserFactory.create(username="test-user")
    response = client.post(
        "/auth/login",
        data=data,
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json()


@pytest.mark.integration
@pytest.mark.parametrize("mock_verify_password", [True], indirect=True)
@pytest.mark.usefixtures("mock_verify_password", "db")
def test_login_success(client: TestClient):
    "Test how `/auth/login` handles valid credentials"

    user: AuthedUser = AuthedUserFactory.create()
    response = client.post(
        "/auth/login",
        data={
            "username": user.username,
            "password": "password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == HTTPStatus.OK, response.json()

    response_json = response.json()
    assert response_json

    assert "access_token" in response_json
    assert "refresh_token" in response_json
