from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy import select
from httpx import AsyncClient
import pytest

from app.models.user_model import AuthedUser
from tests.factories.user import AuthedUserFactory

pytestmark = [pytest.mark.slow]


@pytest.mark.integration
@pytest.mark.parametrize(
    "data",
    (
        {
            "username": "123",
            "email": "test@example.com",
            "password": "securePassword123",
        },
        {
            "username": "me",
            "email": "test@example.com",
            "password": "securePassword123",
        },
        {
            "username": "very-long-username-that-is-way-over-30-characters",
            "email": "test@example.com",
            "password": "securePassword123",
        },
        {
            "username": "test-user",
            "email": "dskasd,asdas",
            "password": "securePassword123",
        },
        {
            "username": "test-user",
            "email": "test@example.com",
            "password": "Password",
        },
        {
            "username": "test-user",
            "email": "test@example.com",
            "password": "password123",
        },
        {
            "username": "test-user",
            "email": "test@example.com",
            "password": "PASSWORD123",
        },
        {
            "username": "test-user",
            "email": "test@example.com",
            "password": "123",
        },
    ),
    ids=[
        "username is just numbers",
        "usename is 'me'",
        "username too long",
        "bad email",
        "weak password - no numbers",
        "weak password - no capital letters",
        "weak password - no lower case letters",
        "weak password - just numbers",
    ],
)
@pytest.mark.usefixtures("db")
async def test_signup_params(async_client: AsyncClient, data: dict):
    """Test how `/auth/signup` handles bad arguments"""

    async with async_client as ac:
        response = await ac.post("/auth/signup", json=data)

    assert (
        response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    ), response.json()


@pytest.mark.integration
async def test_signup_success(async_client: AsyncClient, db: Session):
    """Test if `/auth/signup` works in creating the user when valid arugments are provided"""

    async with async_client as ac:
        response = await ac.post(
            "/auth/signup",
            json={
                "username": "test-username",
                "email": "test@example.com",
                "password": "securePassword123",
            },
        )
    assert response.status_code == HTTPStatus.CREATED, response.json()

    user = db.execute(select(AuthedUser)).scalar_one()
    assert user.username == "test-username"
    assert user.email == "test@example.com"


@pytest.mark.integration
@pytest.mark.parametrize(
    "data",
    (
        {
            "username": "different-test-user",
            "email": "test@example.com",
            "password": "securePassword123",
        },
        {
            "username": "test-user",
            "email": "different-test@example.com",
            "password": "securePassword123",
        },
    ),
    ids=["email conflict", "username conflict"],
)
@pytest.mark.usefixtures("db")
async def test_signup_conflict(async_client: AsyncClient, data: dict):
    """Test how `/auth/signup` handles username / email conflicts"""

    AuthedUserFactory.create(username="test-user", email="test@example.com")
    async with async_client as ac:
        response = await ac.post("/auth/signup", json=data)

    assert response.status_code == HTTPStatus.CONFLICT, response.json()
