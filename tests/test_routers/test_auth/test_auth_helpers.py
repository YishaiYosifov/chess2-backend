from http import HTTPStatus

from httpx import AsyncClient
import pytest

from app.schemas.config_schema import CONFIG
from app.services.jwt_service import create_access_token


class TestIsFresh:
    @pytest.mark.parametrize("is_fresh", [True, False])
    async def test_with_token(self, async_client: AsyncClient, is_fresh: bool):
        access_token = create_access_token(
            CONFIG.secret_key, CONFIG.jwt_algorithm, 1, fresh=is_fresh
        )

        async with async_client as ac:
            response = await ac.get(
                "/auth/is-fresh", cookies={"access_token": access_token}
            )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == is_fresh

    async def test_no_token(self, async_client: AsyncClient):
        async with async_client as ac:
            response = await ac.get("/auth/is-fresh")

        assert response.status_code == HTTPStatus.OK
        assert not response.json()
