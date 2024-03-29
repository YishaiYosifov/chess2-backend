from datetime import timedelta
from typing import Sequence

from _pytest.fixtures import SubRequest
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from sqlalchemy import select
import pytest

from app.models.user_model import AuthedUser, GuestUser
from tests.factories.user import AuthedUserFactory, GuestUserFactory
from tests.utils import mocks
from app.crud import user_crud


@pytest.mark.integration
class TestCreateGuest:
    @pytest.fixture
    def mock_token(self, request: SubRequest, mocker: MockerFixture):
        """
        A fixture for providing a mock guest token.
        Takes a token or a sequence of tokens from the request param.
        If the tokens were not given, it will use the default one.
        """

        new_token: str | Sequence[str] = getattr(
            request, "param", "testing testing testing"
        )

        mock_truncated_uuid = mocker.patch.object(
            user_crud.common, "truncated_uuid"
        )
        if isinstance(new_token, str):
            mock_truncated_uuid.return_value = new_token
        else:
            mock_truncated_uuid.side_effect = new_token

        return new_token

    def test_create_success(self, db: Session, mock_token: str):
        user_crud.create_guest(db)
        guest = db.execute(select(GuestUser)).scalar_one()
        assert guest.username == f"Guest-{mock_token}"

    @pytest.mark.parametrize(
        "mock_token", [("token one", "token two")], indirect=True
    )
    def test_duplicate_token(
        self, db: Session, mocker: MockerFixture, mock_token: tuple[str, str]
    ):
        """
        Test that the `create_guest` crud function will not attempt
        to create a user with a duplicate username
        """

        mocker.patch.object(
            user_crud,
            "get_by_username",
            new=lambda db, username: username == f"Guest-{mock_token[0]}",
        )

        guest = user_crud.create_guest(db)
        assert guest.username == f"Guest-{mock_token[1]}"


@pytest.mark.integration
class TestDeleteInactiveGuests:
    def test_dont_delete_active(self, db: Session, mocker: MockerFixture):
        """Test if the `delete_inactive_guest` crud function ignores all active guests"""

        fixed_datetime, _ = mocks.fix_time(user_crud, mocker)
        GuestUserFactory.create(last_refreshed_token=fixed_datetime)

        user_crud.delete_inactive_guests(db, delete_minutes=10)

        db.execute(select(GuestUser)).scalar_one()

    def test_delete_inactive(self, db: Session, mocker: MockerFixture):
        """Test if the `delete_inactive_guest` crud function succesfully delete all inactive guests"""

        fixed_datetime, _ = mocks.fix_time(user_crud, mocker)
        GuestUserFactory.create(
            last_refreshed_token=fixed_datetime - timedelta(minutes=15)
        )

        user_crud.delete_inactive_guests(db, delete_minutes=10)

        assert not db.execute(select(GuestUser)).all()

    def test_doesnt_delete_registered(self, db: Session, mocker: MockerFixture):
        """Test if the `delete_inactive_guest` crud function ignores all authorized users"""

        fixed_datetime, _ = mocks.fix_time(user_crud, mocker)
        AuthedUserFactory.create(
            last_refreshed_token=fixed_datetime - timedelta(minutes=15)
        )

        user_crud.delete_inactive_guests(db, delete_minutes=10)

        assert db.execute(select(AuthedUser)).scalar_one()
