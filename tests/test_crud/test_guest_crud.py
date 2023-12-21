from typing import Sequence

from _pytest.fixtures import SubRequest
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from sqlalchemy import select
import pytest

from app.models.user_model import GuestUser
from tests.factories.user import GuestFactory
from app.crud import guest_crud


@pytest.mark.integration
class TestGuestUsernameTokenExists:
    def test_exists(self, db: Session):
        GuestFactory.create(username="Guest-TestToken")
        assert guest_crud.username_token_exists(db, "TestToken")

    def test_doesnt_exist(self, db: Session):
        assert not guest_crud.username_token_exists(db, "TestToken")


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
            guest_crud.common, "truncated_uuid"
        )
        if isinstance(new_token, str):
            mock_truncated_uuid.return_value = new_token
        else:
            mock_truncated_uuid.side_effect = new_token

        return new_token

    def test_create_success(self, db: Session, mock_token: str):
        guest_crud.create_guest(db)
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
            guest_crud,
            "username_token_exists",
            new=lambda db, token: token == mock_token[0],
        )

        guest = guest_crud.create_guest(db)
        assert guest.username == f"Guest-{mock_token[1]}"
