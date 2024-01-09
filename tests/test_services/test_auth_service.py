from _pytest.fixtures import SubRequest
from fastapi import HTTPException
import pytest

from app.services.auth_service import OAuth2PasswordBearerCookie


@pytest.mark.unit
class TestOAuth2PasswordBearerCookie:
    @pytest.fixture
    def oauth2_bearer_cookie(self, request: SubRequest):
        return OAuth2PasswordBearerCookie(
            "auth/login", auto_error=getattr(request, "param", False)
        )

    @pytest.mark.parametrize(
        "scheme, token, success",
        [
            ("Bearer", "", False),
            ("Basic", "token", False),
            ("Bearer", "token", True),
        ],
    )
    def test_get_from_header(
        self,
        oauth2_bearer_cookie: OAuth2PasswordBearerCookie,
        scheme: str,
        token: str,
        success: bool,
    ):
        """
        Test if it can get the token from the header.
        Also tests if the class makes sure it's a bearer token.
        """

        returned_tokens = oauth2_bearer_cookie(auth_header=f"{scheme} {token}")

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
        access_token: str | None,
        refresh_token: str | None,
    ):
        """Test if it can get the access and refresh token individually from the cookies."""

        returned_tokens = oauth2_bearer_cookie(
            access_token_cookie=access_token,
            refresh_token_cookie=refresh_token,
        )

        assert returned_tokens.access_token == access_token
        assert returned_tokens.refresh_token == refresh_token

    def test_auto_error(
        self,
        oauth2_bearer_cookie: OAuth2PasswordBearerCookie,
    ):
        """Test if it respects auto_error"""

        oauth2_bearer_cookie.auto_error = True
        with pytest.raises(HTTPException):
            oauth2_bearer_cookie()
