from contextlib import nullcontext
from typing import Type

from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.orm import object_session
from factory import post_generation, SubFactory, Faker

from app.models.games.runtime_player_info import RuntimePlayerInfo
from app.utils.user_setup import setup_user
from app.constants.enums import Variants, Colors
from app.models.rating import Rating
from tests.factories import BaseMetaFactory, BaseMeta
from app.models.user import User
from tests.utils import mock_hash


class UserFactory(SQLAlchemyModelFactory, metaclass=BaseMetaFactory[User]):
    class Meta(BaseMeta):
        model = User

    username = Faker("name")
    email = Faker("email")
    hashed_password = "password"

    mock_hash = True

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

    @classmethod
    def _create(cls, model_class: Type[User], *args, **kwargs) -> User:
        """
        Create the user and mock the hash if necessary.
        If the hash is mocked, the default hash will be for the password
        """

        do_mock_hash = kwargs.pop("mock_hash", cls.mock_hash)
        with mock_hash() if do_mock_hash else nullcontext():
            return super()._create(model_class, *args, **kwargs)


class RuntimePlayerInfoFactory(
    SQLAlchemyModelFactory,
    metaclass=BaseMetaFactory[RuntimePlayerInfo],
):
    class Meta(BaseMeta):
        model = RuntimePlayerInfo

    color = Colors.WHITE
    user = SubFactory(UserFactory)
    time_remaining = 600
