from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select
import pytest

from tests.factories.user import UserFactory
from app.models.user import User


@pytest.mark.parametrize(
    "data",
    [
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
    ],
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
def test_signup_params(client: TestClient, data: dict):
    """Test how `/auth/signup` handles bad arguments"""

    response = client.post("/auth/signup", json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.json()


@pytest.mark.usefixtures("mock_hash")
def test_signup_success(client: TestClient, db: Session):
    """Test if `/auth/signup` works in creating the user when valid arugments are provided"""

    response = client.post(
        "/auth/signup",
        json={
            "username": "test-username",
            "email": "test@example.com",
            "password": "securePassword123",
        },
    )
    assert response.status_code == HTTPStatus.CREATED, response.json

    user = db.execute(select(User)).scalar_one()
    assert user.username == "test-username"
    assert user.email == "test@example.com"


@pytest.mark.parametrize(
    "data",
    [
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
    ],
    ids=["email conflict", "username conflict"],
)
def test_signup_conflict(client: TestClient, db: Session, data: dict):
    """Test how `/auth/signup` handles username / email conflicts"""

    UserFactory.create(session=db, username="test-user", email="test@example.com")
    response = client.post("/auth/signup", json=data)
    assert response.status_code == HTTPStatus.CONFLICT, response.json
