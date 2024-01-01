from io import BytesIO

from fastapi.testclient import TestClient
import pytest

from tests.factories.user import AuthedUserFactory
from tests.utils import mocks


@pytest.mark.usefixtures("db")
def atest_upload_pfp(client: TestClient):
    user = AuthedUserFactory.create()
    buffer = BytesIO(
        b"RIFF$\x00\x00\x00WEBPVP8 \x18\x00\x00\x000\x01\x00\x9d\x01*"
        b"\x01\x00\x01\x00\x01@&%\xa4\x00\x03p\x00\xfe\xfd6h\x00"
    )

    with mocks.mock_login(user):
        print(
            client.put(
                "/settings/upload-profile-picture",
                files={"pfp": buffer.getvalue()},
            ).json()
        )
