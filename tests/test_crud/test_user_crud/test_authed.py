from pytest_mock.plugin import MockType
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
import pytest

from app.models.user_model import AuthedUser
from tests.factories.user import AuthedUserFactory
from app.services import auth_service
from app.schemas import user_schema
from app.crud import user_crud


@pytest.mark.unit
class TestAuthenticate:
    @pytest.fixture
    def mock_get_by_username(self, mocker: MockerFixture):
        return mocker.patch.object(user_crud, "get_by_username")

    @pytest.fixture
    def mock_verify_password(self, mocker: MockerFixture):
        return mocker.patch.object(auth_service, "verify_password")

    def test_authenticate_user_exists_correct_password(
        self,
        mocker: MockerFixture,
        mock_get_by_username: MockType,
        mock_verify_password: MockType,
    ):
        """Test if it calls everything correctly and returns the user"""

        user: AuthedUser = AuthedUserFactory.build()
        mock_get_by_username.return_value = user
        mock_verify_password.return_value = True

        db = mocker.MagicMock()
        fetched_user = user_crud.authenticate(db, user.username, "luka")

        assert fetched_user == user
        mock_get_by_username.assert_called_once_with(
            db, user.username, AuthedUser
        )
        mock_verify_password.assert_called_once_with(
            "luka", user.hashed_password
        )

    def test_authenticaticate_wrong_password(
        self,
        mocker: MockerFixture,
        mock_get_by_username: MockType,
        mock_verify_password: MockType,
    ):
        """Test that a user is not returned if the password is wrong"""

        user: AuthedUser = AuthedUserFactory.build()
        mock_get_by_username.return_value = user
        mock_verify_password.return_value = False

        fetched_user = user_crud.authenticate(
            mocker.MagicMock(),
            user.username,
            "luka",
        )

        assert not fetched_user

    def test_authenticate_wrong_username(
        self,
        mocker: MockerFixture,
        mock_get_by_username: MockType,
        mock_verify_password: MockType,
    ):
        """Test that None is returned if the user was not found"""

        mock_get_by_username.return_value = None
        mock_verify_password.return_value = True
        fetched_user = user_crud.authenticate(
            mocker.MagicMock(),
            "wrong username",
            "luka",
        )

        assert not fetched_user


@pytest.mark.integration
def test_create_authed_user(db: Session, mocker: MockerFixture):
    """Test that a user is created with the correct username, email hash hash"""

    # Mocking in an integration test because hash_password is slow
    # and I am already integration testing it in the signup tests
    mocker.patch.object(auth_service, "hash_password", return_value="mock hash")

    user = user_crud.create_authed(
        db,
        user_schema.UserIn(
            username="testuser",
            email="test@example.com",
            password="securePassword123",
        ),
    )

    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password == "mock hash"
