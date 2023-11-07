from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest

from tests.factories.user import UserFactory


@pytest.mark.parametrize(
    "data, mock_verify_password",
    [
        [{"username": "non-existing-user", "password": "password"}, False],
        [{"username": "username", "password": "bad password"}, False],
    ],
    indirect=["mock_verify_password"],
)
@pytest.mark.usefixtures("mock_verify_password")
def test_login_fail(db: Session, client: TestClient, data):
    """Test how `/auth/login` handles non existing credentials"""

    UserFactory.create(session=db, username="test-username")
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

    assert "accessToken" in response_json
    assert "refreshToken" in response_json
