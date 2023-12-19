from unittest.mock import MagicMock

from _pytest.fixtures import SubRequest
from pytest_mock import MockerFixture
from fastapi import HTTPException
import pytest

from app.services.auth_service import OAuth2PasswordBearerCookie
from app.services import auth_service


@pytest.mark.unit
class TestOAuth2PasswordBearerCookie:
    @pytest.fixture
    def oauth2_bearer_cookie(self, request: SubRequest):
        return OAuth2PasswordBearerCookie(
            "auth/login", auto_error=getattr(request, "param", False)
        )

    @pytest.fixture
    def fastapi_request(self, mocker: MockerFixture):
        return mocker.MagicMock(headers={}, cookies={})

    @pytest.mark.parametrize(
        "scheme, token, success",
        [
            ("Bearer", None, False),
            ("Basic", "token", False),
            ("Bearer", "token", True),
        ],
    )
    def test_get_from_header(
        self,
        oauth2_bearer_cookie: OAuth2PasswordBearerCookie,
        fastapi_request: MagicMock,
        mocker: MockerFixture,
        scheme: str,
        token: str | None,
        success: bool,
    ):
        """
        Test if it can get the token from the header.
        Also tests if the class makes sure it's a bearer token.
        """

        fastapi_request.headers["Authorization"] = token
        get_auth_params_mock = mocker.patch.object(
            auth_service.fastapi_security_utils,
            "get_authorization_scheme_param",
            return_value=(scheme, token),
        )

        returned_tokens = oauth2_bearer_cookie(fastapi_request)

        get_auth_params_mock.assert_called_with(token)

        if success:
            assert returned_tokens.access_token == token
            assert returned_tokens.refresh_token == token
        else:
            assert not returned_tokens.access_token
            assert not returned_tokens.refresh_token

    @pytest.mark.parametrize(
        "access_token, refresh_token",
        [(None, None), ("token", None), (None, "token"), ("access", "refresh")],
    )
    def test_get_from_cookie(
        self,
        oauth2_bearer_cookie: OAuth2PasswordBearerCookie,
        fastapi_request: MagicMock,
        access_token: str | None,
        refresh_token: str | None,
    ):
        """Test if it can get the access and refresh token individually from the cookies."""

        fastapi_request.cookies["access_token"] = access_token
        fastapi_request.cookies["refresh_token"] = refresh_token

        returned_tokens = oauth2_bearer_cookie(fastapi_request)

        assert returned_tokens.access_token == access_token
        assert returned_tokens.refresh_token == refresh_token

    def test_auto_error(
        self,
        oauth2_bearer_cookie: OAuth2PasswordBearerCookie,
        fastapi_request: MagicMock,
    ):
        """Test if it respects auto_error"""

        oauth2_bearer_cookie.auto_error = True
        with pytest.raises(HTTPException):
            oauth2_bearer_cookie(fastapi_request)
