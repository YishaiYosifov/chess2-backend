from io import BytesIO

from fastapi.testclient import TestClient
import pytest

from app.models.user_model import User
from tests.factories.user import UserFactory
from tests.utils.common import mock_login
from app.main import app


@pytest.mark.skip
@pytest.mark.usefixtures("db")
def test_upload_pfp(client: TestClient):
    user: User = UserFactory.create()
    buffer = BytesIO(
        b"RIFF$\x00\x00\x00WEBPVP8 \x18\x00\x00\x000\x01\x00\x9d\x01*"
        b"\x01\x00\x01\x00\x01@&%\xa4\x00\x03p\x00\xfe\xfd6h\x00"
    )

    with mock_login(app, user):
        print(
            client.put(
                "/profile/me/upload-profile-picture",
                files={"pfp": buffer.getvalue()},
            ).json()
        )
