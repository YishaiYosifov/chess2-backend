from unittest.mock import patch, MagicMock
from contextlib import nullcontext
from datetime import timedelta, datetime

from fastapi import HTTPException
import pytest

from app.schemas.config_schema import Settings
from app.models.user_model import User
from tests.factories.user import UserFactory
from app.services import settings_service
from tests import constants


@patch.object(settings_service.auth_service, "hash_password")
def test_password_setting(mock_hash_password: MagicMock):
    """Test if the password setting hashes correctly"""

    user: User = UserFactory.build()

    mocked_hash = "mocked hash"
    mock_hash_password.return_value = mocked_hash
    settings_service.PasswordSetting(user).update("new password")
    assert user.hashed_password == mocked_hash


@patch.object(settings_service.EmailSetting, "validate")
@patch.object(settings_service.email_verification, "send_verification_email")
def test_email_setting(
    mock_email_verification: MagicMock,
    mock_validate: MagicMock,
    settings: Settings,
):
    """Test if the email setting updates the email correctly and sends the verification email"""

    user: User = UserFactory.build()
    new_email = "test@example.com"

    mocked_db = MagicMock()
    settings_service.EmailSetting(mocked_db, user, settings.verification_url).update(
        new_email
    )

    assert user.email == new_email
    assert not user.is_email_verified
    mock_email_verification.assert_called_once_with(
        new_email, settings.verification_url
    )


@pytest.fixture
def username_setting(settings: Settings):
    """Create an instance of the username setting service"""

    user = UserFactory.build()
    mocked_db = MagicMock()
    return settings_service.UsernameSetting(
        mocked_db, user, timedelta(days=settings.edit_username_every_days)
    )


@pytest.mark.parametrize(
    "username_last_changed, success",
    [
        (constants.FIXED_DATETIME - timedelta(days=365), True),
        (constants.FIXED_DATETIME - timedelta(days=31), True),
        (constants.FIXED_DATETIME - timedelta(days=29), False),
        (constants.FIXED_DATETIME - timedelta(days=0), False),
    ],
    ids=str,
)
@patch.object(settings_service, "datetime")
@patch.object(settings_service, "user_crud", autospec=True)
def test_username_setting_validate(
    mock_crud: MagicMock,
    mock_datetime: MagicMock,
    username_last_changed: datetime,
    success: bool,
    username_setting: settings_service.UsernameSetting,
):
    """Test if the username setting prevents rapid username changes"""

    mock_datetime.utcnow.return_value = constants.FIXED_DATETIME
    username_setting.user.username_last_changed = username_last_changed
    with nullcontext() if success else pytest.raises(HTTPException):
        username_setting.validate("test user")


@patch.object(settings_service, "datetime")
@patch.object(settings_service.UsernameSetting, "validate")
def test_username_setting(
    mock_validate: MagicMock,
    mock_datetime: MagicMock,
    username_setting: settings_service.UsernameSetting,
):
    """Test if the username setting updates the username correctly"""

    mock_datetime.utcnow.return_value = constants.FIXED_DATETIME

    new_username = "test-username"
    user = username_setting.user
    username_setting.update(new_username)

    assert user.username == new_username
    assert user.username_last_changed == constants.FIXED_DATETIME
