from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
import pytest

from app.models.user_model import AuthedUser
from tests.factories.user import AuthedUserFactory
from app.schemas import user_schema
from app.crud import user_crud


@pytest.mark.slow
@pytest.mark.unit
class TestAuthenticate:
    def test_authenticate_user_exists_and_correct_password(
        self, db: Session, mocker: MockerFixture
    ):
        user: AuthedUser = AuthedUserFactory.create()
        fetched_user = user_crud.authenticate(
            db, user.username, password="luka"
        )

        assert fetched_user == user

    def test_authenticaticate_wrong_password(self, db: Session):
        user: AuthedUser = AuthedUserFactory.create()
        fetched_user = user_crud.authenticate(
            db, user.username, "wrong password"
        )

        assert not fetched_user

    def test_authenticate_wrong_username(self, db: Session):
        AuthedUserFactory.create()
        fetched_user = user_crud.authenticate(db, "wrong username", "luka")

        assert not fetched_user


@pytest.mark.integration
@pytest.mark.slow
def test_create_authed_user(db: Session):
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
    assert (
        user_crud.authenticate(db, user.username, "securePassword123") == user
    )
