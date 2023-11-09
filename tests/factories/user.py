from sqlalchemy.orm import object_session
from factory import post_generation, SubFactory, Faker

from app.models.games.runtime_player_info import RuntimePlayerInfo
from app.services.auth_service import hash_password
from app.utils.user_setup import setup_user
from app.constants.enums import Variants, Colors
from app.models.rating import Rating
from tests.factories import BaseSQLAlchemyModelFactory
from app.models.user import User


class UserFactory(BaseSQLAlchemyModelFactory[User]):
    class Meta:
        model = User

    username = Faker("name")
    email = Faker("email")
    hashed_password = "$2b$12$faL2dTvq1ysp.1rduW1t0.QE7PNa7aYzNZmNSmkyFu.RKi6FbIxJe"

    @post_generation
    def rating_variants(obj: User, create: bool, extracted: list[Variants], **kwargs):  # type: ignore
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
    def setup(obj: User, create: bool, extracted: list[Variants], **kwargs):  # type: ignore
        session = object_session(obj)
        if not create or not extracted or not session:
            return

        setup_user(session, obj)

    @post_generation
    def password(obj: User, create: bool, extracted: str, **kwargs):  # type: ignore
        if not create or not extracted:
            return

        obj.hashed_password = hash_password(extracted)


class RuntimePlayerInfoFactory(BaseSQLAlchemyModelFactory[RuntimePlayerInfo]):
    class Meta:
        model = RuntimePlayerInfo

    color = Colors.WHITE
    user = SubFactory(UserFactory)
    time_remaining = 600
