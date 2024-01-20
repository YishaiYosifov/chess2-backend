from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy import select
from httpx import AsyncClient
import pytest

from app.models.user_model import GuestUser


@pytest.mark.anyio
@pytest.mark.integration
async def test_create_guest_account(async_client: AsyncClient, db: Session):
    async with async_client as ac:
        response = await ac.get("/auth/guest-account")

    assert response.status_code == HTTPStatus.CREATED

    created_guest = db.execute(select(GuestUser)).scalar_one()
    assert created_guest.username.startswith("Guest-")
    assert response.json()["access_token"]
