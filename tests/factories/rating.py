from datetime import timedelta, datetime

import factory

from tests.utils.factory_model import TypedSQLAlchemyFactory
from app.models.rating_model import Rating
from app.models.user_model import AuthedUser
from tests.conftest import TestScopedSession
from app import enums

from .user import AuthedUserFactory


class RatingFactory(TypedSQLAlchemyFactory[Rating]):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = Rating

    user = factory.SubFactory(AuthedUserFactory)
    variant = enums.Variant.ANARCHY

    @classmethod
    def create_history(
        cls,
        user: AuthedUser,
        variants: dict[enums.Variant, list[int] | list[int | None] | int],
    ) -> list[Rating]:
        """
        Create a multiple rating entries of a certain variant. The first elo will be the active one.
        The `achieved_at` dates will ascend by one day each rating in a variant.

        :param user: the user for whom the rating history is being created
        :param variants: a dictionary of variants with either:
            - a list of elos (or None to use the default elo value)
            in ascending order (from least to most revent)
            - an amount, how many of these variant ratings to create with the default elo

        :return: a list of the created ratings
        """

        ratings = []
        for variant, elos in variants.items():
            # if elos is an amount, create a list with the correct elos
            elos = [800] * elos if isinstance(elos, int) else elos

            achieved_at = datetime.utcnow() - timedelta(days=len(elos))
            for i, elo in enumerate(elos):
                rating: Rating = cls.create(
                    user=user,
                    variant=variant,
                    elo=elo,
                    is_active=i == 0,
                    achieved_at=achieved_at,
                )
                ratings.append(rating)

                # Make sure the ratings have different dates
                achieved_at += timedelta(days=1)

        cls._meta.sqlalchemy_session.flush()  # type: ignore

        return ratings

    @classmethod
    def create_variant_batch(
        cls, user: AuthedUser, variants: list[enums.Variant]
    ):
        return cls.create_history(user, {variant: 1 for variant in variants})
