from datetime import date
from typing import Any

from sqlalchemy.orm import Session
import pytest

from tests.factories.rating import RatingFactory
from app.models.user_model import User
from tests.factories.user import UserFactory
from app.constants import enums
from tests.utils import common as common_utils
from app.crud import ratings_crud


@pytest.mark.parametrize(
    "user_variants, fetch_variants",
    [
        (
            [enums.Variant.ANARCHY, enums.Variant.CHSS],
            [enums.Variant.ANARCHY, enums.Variant.CHSS],
        ),
        (enums.Variant, [enums.Variant.ANARCHY, enums.Variant.CHSS]),
        (enums.Variant, [enums.Variant.ANARCHY]),
        ([], []),
    ],
    ids=[
        "Some ratings exist, fetch specific variants",
        "All ratings exist, fetch specific variants",
        "All ratings exist, fetch a single variant",
        "No ratings exist, fetch no variants",
    ],
)
class TestRatingsCrudFetch:
    """Test how the ratings crud functions fetch with multiple user / fetch rating variants"""

    def _assert_correct_fetches(
        self,
        fetched: dict[enums.Variant, Any],
        user_variants: list[enums.Variant] | type[enums.Variant],
        fetch_variants: list[enums.Variant] | type[enums.Variant],
    ) -> None:
        """
        Test if there is a mismatch between what ratings the user has,
        what ratings were fetched and the fetch results

        :param fetched: the fetch results
        :param user_variants: the rating variants the user has
        :param fetch_variants: which variants were provided to the fetch function
        :raise AssertionError: unexpecter results for a variant
        """

        user_variants = list(user_variants)
        fetch_variants = list(fetch_variants)

        # If the variant is in both user_variants and fetch_variants, it means it should have been fetched
        expected_variants = common_utils.get_duplicates(user_variants + fetch_variants)
        for variant in enums.Variant:
            should_include = variant in expected_variants
            assert (
                variant in fetched if should_include else variant not in fetched
            ), f"Unexpected results for variant {variant}: " + (
                "not included when should be"
                if should_include
                else "included when shouldn't be"
            )

    def test_fetch_many(
        self,
        db: Session,
        user_variants: list[enums.Variant],
        fetch_variants: list[enums.Variant],
    ):
        """
        Test the `fetch_many` crud function to check if it correctly
        fetches ratings for multiple user / fetch variants
        """

        user: User = UserFactory.create()
        RatingFactory.create_variant_batch(user, user_variants)

        ratings = ratings_crud.fetch_many(db, user, fetch_variants)
        self._assert_correct_fetches(ratings, user_variants, fetch_variants)

        for variant, rating in ratings.items():
            assert rating.variant == variant
            assert rating.user == user
            assert rating.is_active

    def test_fetch_history(
        self,
        db: Session,
        user_variants: list[enums.Variant],
        fetch_variants: list[enums.Variant],
    ):
        """
        Test the `fetch_history` crud function to check if it correctly fetches
        the history (i.e. {variant: list[Rating]})
        """

        elos = [500, 57, 1]
        user: User = UserFactory.create()
        RatingFactory.create_history(user, {variant: elos for variant in user_variants})

        ratings_history = ratings_crud.fetch_history(
            db, user, date(2001, 1, 1), fetch_variants
        )
        self._assert_correct_fetches(ratings_history, user_variants, fetch_variants)

        for fetched_ratings in ratings_history.values():
            for index, rating in enumerate(fetched_ratings):
                assert rating.elo == elos[index]

    def test_fetch_min_max(
        self,
        db: Session,
        user_variants: list[enums.Variant],
        fetch_variants: list[enums.Variant],
    ):
        """
        Test the `fetch_min_max` crud function to check if correctly fetches the
        lowest and highest ratings for multiple user / fetch variants
        """

        origin_elos = [500, 57, 1]
        min_origin_elo = min(origin_elos)
        max_origin_elo = max(origin_elos)

        user: User = UserFactory.create()
        RatingFactory.create_history(
            user, {variant: origin_elos for variant in user_variants}
        )

        ratings_minmax = ratings_crud.fetch_min_max(db, user, fetch_variants)
        self._assert_correct_fetches(ratings_minmax, user_variants, fetch_variants)

        for min_fetched, max_fetched in ratings_minmax.values():
            assert min_fetched == min_origin_elo
            assert max_fetched == max_origin_elo


def test_fetch_many_inactive(db: Session):
    """Test the `fetch_many` crud function to ensure it handles inactive ratings correctly"""

    user: User = UserFactory.create()
    RatingFactory.create(user=user, variant=enums.Variant.ANARCHY)

    user.ratings[0].elo = 700
    db.commit()

    ratings = ratings_crud.fetch_many(db, user, [enums.Variant.ANARCHY])
    assert len(ratings) == 1
    assert ratings[enums.Variant.ANARCHY].elo == 700


def test_fetch_min_max_one_elo(db: Session):
    """Test what `user_crud.fetch_min_max` does when there is only 1 rating entry"""

    user: User = UserFactory.create()
    RatingFactory.create_history(user, {enums.Variant.ANARCHY: [800]})

    ratings_min_max = ratings_crud.fetch_min_max(db, user, [enums.Variant.ANARCHY])
    results_min, results_max = ratings_min_max.get(enums.Variant.ANARCHY, (None, None))

    assert results_min == 800
    assert results_max == 800
