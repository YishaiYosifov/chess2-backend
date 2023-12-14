from datetime import timedelta, datetime

from pytest_mock import MockerFixture
import pytest

from app.schemas.config_schema import Settings
from app.services import auth_service
from tests.utils import mocks


@pytest.mark.unit
def test_encode_jwt_token(
    mocker: MockerFixture,
    settings: Settings,
):
    """Test the encoding of a jwt token"""

    fixed_datetime = datetime(2023, 6, 9)
    fixed_timestamp = 69

    # Setup mocks
    mock_jwt_encode = mocker.patch.object(auth_service.jwt, "encode")
    fixed_datetime, fixed_timestamp = mocks.fix_time(auth_service, mocker)

    expires_in_delta = timedelta(minutes=30)
    auth_service._encode_jwt_token(
        settings.secret_key,
        settings.jwt_algorithm,
        {"sub": 1},
        expires_in_delta,
    )

    # Check if the payload was correct
    expected_payload = {
        "exp": fixed_datetime + expires_in_delta,
        "iat": fixed_timestamp,
        "nbf": fixed_timestamp,
        "sub": 1,
    }
    mock_jwt_encode.assert_called_once_with(
        expected_payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


@pytest.mark.unit
def test_create_access_token(mocker: MockerFixture, settings: Settings):
    """Test creating an access token"""

    user_id = 123
    expires_in_minutes = 69
    mock_encode = mocker.patch.object(auth_service, "_encode_jwt_token")

    auth_service.create_access_token(
        settings.secret_key,
        settings.jwt_algorithm,
        user_id,
        expires_in_minutes,
    )
    mock_encode.assert_called_once_with(
        settings.secret_key,
        settings.jwt_algorithm,
        {"sub": str(user_id), "type": "access", "fresh": False},
        timedelta(minutes=expires_in_minutes),
    )


@pytest.mark.unit
def test_create_refresh_token(
    mocker: MockerFixture,
    settings: Settings,
):
    """Test creating a jwt token"""

    user_id = 123
    expires_in_days = 69
    jti = "some random string"

    mocker.patch.object(auth_service.uuid, "uuid4", return_value=jti)
    mock_encode = mocker.patch.object(auth_service, "_encode_jwt_token")

    auth_service.create_refresh_token(
        settings.secret_key,
        settings.jwt_algorithm,
        user_id,
        expires_in_days,
    )

    mock_encode.assert_called_once_with(
        settings.secret_key,
        settings.jwt_algorithm,
        {"sub": str(user_id), "type": "refresh", "jti": jti},
        timedelta(days=expires_in_days),
    )
