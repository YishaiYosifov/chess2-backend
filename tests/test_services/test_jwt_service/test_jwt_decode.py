from unittest.mock import MagicMock

from pytest_mock import MockerFixture
import pytest

from app.schemas.config_schema import Config
from app.services import jwt_service


@pytest.mark.unit
def test_decode_jwt_token(mocker: MockerFixture, config: Config):
    """
    Test the helper decode jwt token function.
    Check if it handles options correctly.
    """

    mock_jwt_decode = mocker.patch.object(jwt_service.jwt, "decode")

    jwt_service._decode_jwt_token(
        config.secret_key,
        config.jwt_algorithm,
        "token",
        {"require_exp": False, "require_jti": True},
    )

    expected_options = {
        "require_exp": False,
        "require_iat": True,
        "require_nbf": True,
        "require_jti": True,
    }
    mock_jwt_decode.assert_called_once_with(
        "token",
        "test-secret-key",
        algorithms=["HS256"],
        options=expected_options,
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload, success, token_type",
    (
        [
            {"type": "access", "sub": "1"},
            True,
            "access",
        ],
        [
            {"type": "refresh", "sub": "1", "jti": "random string"},
            True,
            "refresh",
        ],
        [
            {"type": "refresh", "sub": "1", "jti": "random string"},
            False,
            "access",
        ],
        [
            {"type": "access", "sub": "1", "jti": "random string"},
            False,
            "refresh",
        ],
    ),
    ids=[
        "token type: access, correct payload",
        "token type: access, incorrect payload",
        "token type: refresh, correct payload",
        "token type: refresh, incorrect payload",
    ],
)
def test_decode_tokens(
    mocker: MockerFixture,
    payload: dict[str, str],
    success: bool,
    token_type: str,
    config: Config,
):
    """Try to decode tokens with correct and incorrect types"""

    mocker.patch.object(jwt_service, "_decode_jwt_token", return_value=payload)
    mocker.patch.object(jwt_service, "_get_jwt_indentity", return_value=1)
    mocker.patch.object(
        jwt_service, "_check_token_revocation", return_value=False
    )

    user_id = (
        jwt_service.decode_access_token(
            config.secret_key,
            config.jwt_algorithm,
            "token",
        )
        if token_type == "access"
        else jwt_service.decode_refresh_token(
            config.secret_key,
            config.jwt_algorithm,
            MagicMock(),
            "token",
        )
    )
    assert (user_id and success) or (not user_id and not success)
