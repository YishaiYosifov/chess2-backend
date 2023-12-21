from factory.alchemy import SQLAlchemyModelFactory
from factory import post_generation, SubFactory, Faker

from app.models.games.runtime_player_info_model import RuntimePlayerInfo
from app.services.auth_service import hash_password
from app.models.user_model import AuthedUser, GuestUser
from tests.conftest import TestScopedSession
from app.constants import enums


class GuestFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = GuestUser

    username = Faker("name")


class AuthedUserFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = AuthedUser

    username = Faker("name")
    email = Faker("email")
    hashed_password = (
        "$2b$12$faL2dTvq1ysp.1rduW1t0.QE7PNa7aYzNZmNSmkyFu.RKi6FbIxJe"
    )

    @post_generation
    def password(obj: AuthedUser, create: bool, extracted: str, **kwargs):  # type: ignore
        if not create or not extracted:
            return

        obj.hashed_password = hash_password(extracted)


class PlayerFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = RuntimePlayerInfo

    color = enums.Color.WHITE
    user = SubFactory(AuthedUserFactory)
    time_remaining = 600
