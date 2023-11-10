from unittest.mock import patch, MagicMock
from datetime import timedelta, datetime

from app.schemas.config import Settings
from app.services import auth_service


@patch.object(auth_service.jwt, "encode")
@patch.object(auth_service, "datetime")
@patch.object(auth_service, "time")
def test_encode_jwt_token(
    mock_time: MagicMock,
    mock_datetime: MagicMock,
    mock_jwt_encode: MagicMock,
    settings: Settings,
):
    """Test the encoding of a jwt token"""

    fixed_datetime = datetime(2023, 1, 1)
    fixed_timestamp = 69

    # Mock anything related to time
    mock_datetime.utcnow = MagicMock(return_value=fixed_datetime)
    mock_time.time = MagicMock(return_value=fixed_timestamp)

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


@patch.object(auth_service, "_encode_jwt_token")
def test_create_access_token(mock_encode: MagicMock, settings: Settings):
    """Test creating an access token"""

    user_id = 123
    expires_in_minutes = 69

    auth_service.create_access_token(
        settings.secret_key,
        settings.jwt_algorithm,
        user_id,
        expires_in_minutes,
    )
    mock_encode.assert_called_once_with(
        settings.secret_key,
        settings.jwt_algorithm,
        {"sub": str(user_id), "type": "access"},
        timedelta(minutes=expires_in_minutes),
    )


@patch.object(auth_service, "_encode_jwt_token")
@patch.object(auth_service, "uuid")
def test_create_refresh_token(
    mock_uuid: MagicMock,
    mock_encode: MagicMock,
    settings: Settings,
):
    """Test creating a jwt token"""

    user_id = 123
    expires_in_days = 69
    jti = "some random string"

    mock_uuid.uuid4 = MagicMock(return_value=jti)
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
