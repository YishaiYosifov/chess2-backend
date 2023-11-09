from unittest.mock import patch, MagicMock

import pytest

from app.services import auth_service


@patch.object(auth_service.jwt, "decode")
def test_decode_jwt_token(mock_jwt_decode: MagicMock):
    """
    Test the helper decode jwt token function.
    Check if it handles options correctly.
    """
    auth_service._decode_jwt_token("token", {"require_exp": False, "require_jti": True})

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


@pytest.mark.parametrize(
    "payload, success, token_type",
    [
        (
            {"type": "access", "sub": "1"},
            True,
            "access",
        ),
        (
            {"type": "refresh", "sub": "1", "jti": "random string"},
            True,
            "refresh",
        ),
        (
            {"type": "refresh", "sub": "1", "jti": "random string"},
            False,
            "access",
        ),
        (
            {"type": "access", "sub": "1", "jti": "random string"},
            False,
            "refresh",
        ),
    ],
    ids=[
        "token type: access, correct payload",
        "token type: access, incorrect payload",
        "token type: refresh, correct payload",
        "token type: refresh, incorrect payload",
    ],
)
@patch.object(auth_service, "_decode_jwt_token")
@patch.object(auth_service, "_get_jwt_indentity")
@patch.object(auth_service, "_check_token_revocation")
def test_decode_tokens(
    mock_check_revocation: MagicMock,
    mock_get_identity: MagicMock,
    mock_jwt_decode: MagicMock,
    payload: dict[str, str],
    success: bool,
    token_type: str,
):
    """Try to decode tokens with correct and incorrect types"""

    mock_check_revocation.return_value = False
    mock_jwt_decode.return_value = payload
    mock_get_identity.return_value = 1

    user_id = (
        auth_service.decode_access_token("token")
        if token_type == "access"
        else auth_service.decode_refresh_token(MagicMock(), "token")
    )
    assert (user_id and success) or (not user_id and not success)
