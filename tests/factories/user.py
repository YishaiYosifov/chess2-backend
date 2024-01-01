from factory import post_generation, SubFactory, Sequence, Faker

from app.models.games.runtime_player_info_model import RuntimePlayerInfo
from tests.utils.factory_model import TypedSQLAlchemyFactory
from app.services.auth_service import hash_password
from app.models.user_model import AuthedUser, GuestUser
from tests.conftest import TestScopedSession
from app.constants import enums


class GuestUserFactory(TypedSQLAlchemyFactory[GuestUser]):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = GuestUser

    username = Faker("name")


class AuthedUserFactory(TypedSQLAlchemyFactory[AuthedUser]):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = AuthedUser

    user_id = Sequence(lambda n: n)

    username = Faker("name")
    email = Faker("email")
    hashed_password = (
        "$2b$12$faL2dTvq1ysp.1rduW1t0.QE7PNa7aYzNZmNSmkyFu.RKi6FbIxJe"  # luka
    )

    @post_generation
    def password(obj: AuthedUser, create: bool, extracted: str, **kwargs):  # type: ignore
        if not create or not extracted:
            return

        obj.hashed_password = hash_password(extracted)


class PlayerFactory(TypedSQLAlchemyFactory[RuntimePlayerInfo]):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = RuntimePlayerInfo

    color = enums.Color.WHITE
    user = SubFactory(AuthedUserFactory)
    time_remaining = 600
