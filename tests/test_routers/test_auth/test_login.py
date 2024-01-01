from http import HTTPStatus

from httpx import AsyncClient
import pytest

from tests.factories.user import AuthedUserFactory


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.parametrize(
    "data",
    (
        {"username": "non-existing-user", "password": "luka"},
        {"username": "test-user", "password": "bad password"},
    ),
)
@pytest.mark.usefixtures("db")
async def test_login_fail(async_client: AsyncClient, data):
    """Test how `/auth/login` handles non existing credentials"""

    AuthedUserFactory.create(username="test-user")
    async with async_client as ac:
        response = await ac.post(
            "/auth/login",
            data=data,
        )

    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json()


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.usefixtures("db")
async def test_login_success(async_client: AsyncClient):
    "Test how `/auth/login` handles valid credentials"

    user = AuthedUserFactory.create()

    async with async_client as ac:
        response = await ac.post(
            "/auth/login",
            data={
                "username": user.username,
                "password": "luka",
            },
        )

    assert response.status_code == HTTPStatus.OK, response.json()

    response_json = response.json()
    assert response_json

    assert "access_token" in response_json
    assert "refresh_token" in response_json
