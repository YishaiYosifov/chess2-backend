import factory

from app.models.games.live_player_model import LivePlayer
from tests.utils.test_scoped_session import TestScopedSession
from tests.utils.factory_model import TypedSQLAlchemyFactory
from app.services.auth_service import hash_password
from app.models.user_model import AuthedUser, GuestUser
from app import enums


class GuestUserFactory(TypedSQLAlchemyFactory[GuestUser]):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = GuestUser

    username = factory.Faker("name")


class AuthedUserFactory(TypedSQLAlchemyFactory[AuthedUser]):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = AuthedUser

    user_id = factory.Sequence(lambda n: n)

    username = factory.Faker("name")
    email = factory.Faker("email")
    hashed_password = "$argon2id$v=19$m=65536,t=3,p=4$9f6TQfLJyVg0RisM6m2YUw$4e1KxrjDlgZ3CdO6Da19RPg4nMBqQ7g71FIIG3AFzRE"  # luka

    @factory.post_generation
    def password(obj: AuthedUser, create: bool, extracted: str, **kwargs):  # type: ignore
        if not create or not extracted:
            return

        obj.hashed_password = hash_password(extracted)


class PlayerFactory(TypedSQLAlchemyFactory[LivePlayer]):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = LivePlayer

    color = enums.Color.WHITE
    user = factory.SubFactory(AuthedUserFactory)
    time_remaining = 600
