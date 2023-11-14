from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.orm import object_session
from factory import post_generation, SubFactory, Faker

from app.models.games.runtime_player_info_model import RuntimePlayerInfo
from app.services.auth_service import hash_password
from app.models.rating_model import Rating
from app.models.user_model import User
from tests.conftest import ScopedSession
from app.constants import enums


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session_persistence = "commit"
        sqlalchemy_session = ScopedSession
        model = User

    username = Faker("name")
    email = Faker("email")
    hashed_password = "$2b$12$faL2dTvq1ysp.1rduW1t0.QE7PNa7aYzNZmNSmkyFu.RKi6FbIxJe"

    @post_generation
    def rating_variants(obj: User, create: bool, extracted: list[enums.Variant], **kwargs):  # type: ignore
        """
        Generate the required rating for the user based on the provided variants.
        This function will convert the variants into a set, so providing duplicates isn't a problem.
        """

        session = object_session(obj)
        if not create or not extracted or not session:
            return

        for variant in set(extracted):
            session.add(Rating(user=obj, variant=variant))

    @post_generation
    def password(obj: User, create: bool, extracted: str, **kwargs):  # type: ignore
        if not create or not extracted:
            return

        obj.hashed_password = hash_password(extracted)


class RuntimePlayerInfoFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = ScopedSession
        model = RuntimePlayerInfo

    color = enums.Color.WHITE
    user = SubFactory(UserFactory)
    time_remaining = 600
