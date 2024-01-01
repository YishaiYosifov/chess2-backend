from sqlalchemy.orm import Session
import pytest

from tests.factories.user import AuthedUserFactory
from app.services import jwt_service
from app.crud import user_crud


@pytest.mark.integration
def test_get_by_id(db: Session):
    user = AuthedUserFactory.create()
    assert user_crud.get_by_id(db, user.user_id) == user


@pytest.mark.integration
def test_get_by_username(db: Session):
    user = AuthedUserFactory.create(username="test username")
    assert user_crud.get_by_username(db, user.username) == user


@pytest.mark.integration
def test_get_by_email(db: Session):
    user = AuthedUserFactory.create(email="test@example.com")
    assert user_crud.get_by_email(db, user.email) == user


@pytest.mark.integration
class TestGetUser:
    def test_id(self, db: Session):
        """Test that the user is fetched when an id is provided in int and str forms"""

        user = AuthedUserFactory.create()

        assert user_crud.get_user(db, user.user_id) == user
        assert user_crud.get_user(db, str(user.user_id)) == user

    def test_username(self, db: Session):
        """Test that the user i fetched when a username is provided"""

        user = AuthedUserFactory.create(username="test username")
        assert user_crud.get_by_username(db, user.username) == user

    def test_invalid_selector(self, db: Session):
        """Test that a user is not fetched with an invalid selector"""

        AuthedUserFactory.create()
        assert not user_crud.get_by_username(db, "invalid")


@pytest.mark.integration
class TestGetByToken:
    def create_token(self, user_id, is_refresh=False):
        key = "secret key"
        algorithm = "HS256"

        return (
            jwt_service.create_refresh_token(key, algorithm, user_id)
            if is_refresh
            else jwt_service.create_access_token(key, algorithm, user_id)
        )

    @pytest.mark.parametrize("token_type", ["access", "refresh"])
    def test_valid_token(self, db: Session, token_type: str):
        """Test that a user is fetched when the token is valid"""

        is_refresh = token_type == "refresh"

        user = AuthedUserFactory.create()
        token = self.create_token(user.user_id, is_refresh)

        fetched_user = user_crud.get_by_token(
            db,
            "secret key",
            "HS256",
            token,
            refresh=is_refresh,
        )

        assert fetched_user == user

    @pytest.mark.parametrize("token_type", ["access", "refresh"])
    def test_invalid_token(self, db: Session, token_type):
        """Test that a user is not fetched when the token is invalid"""

        AuthedUserFactory.create()
        fetched_user = user_crud.get_by_token(
            db,
            "secret key",
            "HS256",
            "invalid token",
            refresh=token_type == "refresh",
        )

        assert not fetched_user

    def test_access_when_refresh(self, db: Session):
        """
        Test that the user is not fetched a refresh token
        was requested but an access token was given
        """

        user = AuthedUserFactory.create()
        access_token = self.create_token(user.user_id)

        fetched_user = user_crud.get_by_token(
            db,
            "secret key",
            "HS256",
            access_token,
            refresh=True,
        )

        assert not fetched_user
