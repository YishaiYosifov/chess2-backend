from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select
import pytest

from app.models.user_model import GuestUser


@pytest.mark.integration
@pytest.mark.skip
@pytest.mark.usefixtures("mock_hash")
def test_create_guest_account(client: TestClient, db: Session):
    response = client.get("/auth/guest-account")

    assert response.status_code == HTTPStatus.CREATED

    created_guest = db.execute(select(GuestUser)).scalar_one()
    assert created_guest.username.startswith("guest-")
