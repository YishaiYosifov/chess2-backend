from unittest.mock import MagicMock
from contextlib import nullcontext
from datetime import timedelta, datetime

from pytest_mock import MockerFixture
from fastapi import HTTPException
import pytest

from app.schemas.config_schema import Settings
from app.models.user_model import User
from tests.factories.user import UserFactory
from app.services import settings_service
from tests.utils import mocks


@pytest.mark.unit
def test_password_setting(mocker: MockerFixture):
    """Test if the password setting hashes correctly"""

    mocked_hash = "mocked hash"
    mock_hash_password = mocker.patch.object(
        settings_service.auth_service, "hash_password"
    )
    mock_hash_password.return_value = mocked_hash

    user: User = UserFactory.build()

    settings_service.PasswordSetting(user).update("new password")
    assert user.hashed_password == mocked_hash


@pytest.mark.unit
def test_email_setting(
    mocker: MockerFixture,
    settings: Settings,
):
    """Test if the email setting updates the email correctly and sends the verification email"""

    mocker.patch.object(settings_service.EmailSetting, "validate")
    mock_email_verification = mocker.patch.object(
        settings_service.email_verification,
        "send_verification_email",
    )

    user: User = UserFactory.build()
    new_email = "test@example.com"

    mocked_db = MagicMock()
    settings_service.EmailSetting(
        mocked_db, user, settings.verification_url
    ).update(new_email)

    assert user.email == new_email
    assert not user.is_email_verified
    mock_email_verification.assert_called_once_with(
        new_email, settings.verification_url
    )


@pytest.mark.unit
@pytest.mark.usefixtures("fix_datetime")
class TestUsernameSetting:
    fixed_datetime = datetime(2023, 6, 9)

    @pytest.fixture
    def fix_datetime(self, mocker: MockerFixture):
        mocks.fix_time(settings_service, mocker, to=self.fixed_datetime)

    @pytest.fixture
    def username_setting(self, settings: Settings):
        """Create an instance of the username setting service"""

        user = UserFactory.build()
        mocked_db = MagicMock()
        return settings_service.UsernameSetting(
            mocked_db, user, timedelta(days=settings.edit_username_every_days)
        )

    @pytest.mark.parametrize(
        "username_last_changed, success",
        (
            [fixed_datetime - timedelta(days=365), True],
            [fixed_datetime - timedelta(days=31), True],
            [fixed_datetime - timedelta(days=29), False],
            [fixed_datetime - timedelta(days=0), False],
        ),
        ids=str,
    )
    def test_validate(
        self,
        username_setting: settings_service.UsernameSetting,
        username_last_changed: datetime,
        mocker: MockerFixture,
        success: bool,
    ):
        """Test if the username setting prevents rapid username changes"""

        mocker.patch.object(settings_service, "user_crud", autospec=True)

        username_setting.user.username_last_changed = username_last_changed
        with nullcontext() if success else pytest.raises(HTTPException):
            username_setting.validate("test user")

    def test_update(
        self,
        username_setting: settings_service.UsernameSetting,
        mocker: MockerFixture,
    ):
        """Test if the username setting updates the username correctly"""

        mocker.patch.object(settings_service.UsernameSetting, "validate")

        new_username = "test-username"
        user = username_setting.user
        username_setting.update(new_username)

        assert user.username == new_username
        assert user.username_last_changed == self.fixed_datetime
