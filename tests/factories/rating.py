from datetime import timedelta, datetime

from factory.alchemy import SQLAlchemyModelFactory
from factory import SubFactory, Sequence

from app.models.rating_model import Rating
from app.models.user_model import User
from tests.conftest import TestScopedSession
from app.constants import enums

from .user import UserFactory


class RatingFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = Rating

    rating_id = Sequence(lambda n: n)
    user = SubFactory(UserFactory)
    variant = enums.Variant.ANARCHY

    @classmethod
    def create_history(
        cls,
        user: User,
        variants: dict[enums.Variant, list[int] | list[int | None] | int],
    ) -> list[Rating]:
        """
        Create a multiple rating entries of a certain variant. The first elo will be the active one.
        The `achieved_at` dates will descend by one day each rating in a variant.

        :param user: the user for whom the rating history is being created
        :param variants: a dictionary of variants and a list of elos or an amount to create
        :return: a list of the created ratings
        """

        ratings = []
        for variant, elos in variants.items():
            # if elos is an amount, create a list with the correct elos
            elos = [800] * elos if isinstance(elos, int) else elos

            achieved_at = datetime.utcnow()
            for index, elo in enumerate(elos):
                rating: Rating = cls.create(
                    user=user,
                    variant=variant,
                    elo=elo,
                    is_active=index == 0,
                    achieved_at=achieved_at,
                )
                ratings.append(rating)

                # Make sure the ratings have different dates
                achieved_at -= timedelta(days=1)

        cls._meta.sqlalchemy_session.flush()  # type: ignore

        return ratings

    @classmethod
    def create_variant_batch(cls, user: User, variants: list[enums.Variant]):
        return cls.create_history(user, {variant: 1 for variant in variants})
