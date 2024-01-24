from datetime import date
from typing import Sequence, Any

from sqlalchemy.orm import Session
import pytest

from tests.factories.rating import RatingFactory
from tests.factories.user import AuthedUserFactory
from app.constants import enums
from tests.utils import test_common as common_utils
from app.crud import rating_crud

from .conftest import RatingHistory, RatingBatch


def _assert_correct_fetches(
    fetched: dict[enums.Variant, Any],
    user_variants: Sequence[enums.Variant],
    fetch_variants: Sequence[enums.Variant],
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
    expected_variants = common_utils.get_duplicates(
        user_variants + fetch_variants
    )
    for variant in enums.Variant:
        should_include = variant in expected_variants
        assert (
            variant in fetched if should_include else variant not in fetched
        ), f"Unexpected results for variant {variant}: " + (
            "not included when should be"
            if should_include
            else "included when shouldn't be"
        )


TEST_CASES = {
    "argvalues": [
        (
            [enums.Variant.ANARCHY, enums.Variant.CHSS],
            [enums.Variant.ANARCHY, enums.Variant.CHSS],
        ),
        (enums.Variant, [enums.Variant.ANARCHY, enums.Variant.CHSS]),
        (enums.Variant, [enums.Variant.ANARCHY]),
        ([], []),
    ],
    "ids": [
        "Some ratings exist, fetch specific variants",
        "All ratings exist, fetch specific variants",
        "All ratings exist, fetch a single variant",
        "No ratings exist, fetch no variants",
    ],
}


@pytest.mark.integration
class TestFetchMany:
    @pytest.mark.parametrize(
        "rating_batch, fetch_variants",
        indirect=["rating_batch"],
        **TEST_CASES,
    )
    def test_fetch(
        self,
        db: Session,
        rating_batch: RatingBatch,
        fetch_variants: list[enums.Variant],
    ):
        """
        Test the `fetch_many` crud function to check if it correctly
        fetches ratings for multiple user / fetch variants
        """

        ratings = rating_crud.fetch_many(db, rating_batch.user, fetch_variants)
        _assert_correct_fetches(ratings, rating_batch.variants, fetch_variants)

        for variant, rating in ratings.items():
            assert rating.variant == variant
            assert rating.user == rating_batch.user
            assert rating.is_active

    def test_inactive(self, db: Session):
        """Test the `fetch_many` crud function to ensure it handles inactive ratings correctly"""

        user = AuthedUserFactory.create()
        RatingFactory.create(user=user, variant=enums.Variant.ANARCHY)

        user.ratings[0].elo = 700
        db.commit()

        ratings = rating_crud.fetch_many(db, user, [enums.Variant.ANARCHY])
        assert len(ratings) == 1
        assert ratings[enums.Variant.ANARCHY].elo == 700


@pytest.mark.integration
class TestFetchMinMax:
    @pytest.mark.parametrize(
        "rating_history, fetch_variants",
        indirect=["rating_history"],
        **TEST_CASES,
    )
    def test_fetch(
        self,
        db: Session,
        rating_history: RatingHistory,
        fetch_variants: list[enums.Variant],
    ):
        """
        Test the `fetch_min_max` crud function to check if correctly fetches the
        lowest and highest ratings for multiple user / fetch variants
        """

        min_origin_elo = min(rating_history.elos)
        max_origin_elo = max(rating_history.elos)

        ratings_minmax = rating_crud.fetch_min_max(
            db, rating_history.user, fetch_variants
        )
        _assert_correct_fetches(
            ratings_minmax, rating_history.variants, fetch_variants
        )

        for min_fetched, max_fetched in ratings_minmax.values():
            assert min_fetched == min_origin_elo
            assert max_fetched == max_origin_elo

    def test_one_elo(self, db: Session):
        """Test what `user_crud.fetch_min_max` does when there is only 1 rating entry"""

        user = AuthedUserFactory.create()
        RatingFactory.create_history(user, {enums.Variant.ANARCHY: [800]})

        ratings_min_max = rating_crud.fetch_min_max(
            db, user, [enums.Variant.ANARCHY]
        )
        results_min, results_max = ratings_min_max.get(
            enums.Variant.ANARCHY, (None, None)
        )

        assert results_min == 800
        assert results_max == 800


@pytest.mark.integration
@pytest.mark.parametrize(
    "rating_history, fetch_variants",
    indirect=["rating_history"],
    **TEST_CASES,
)
def test_fetch_history(
    db: Session,
    rating_history: RatingHistory,
    fetch_variants: list[enums.Variant],
):
    """
    Test the `fetch_history` crud function to check if it correctly fetches
    the history (i.e. {variant: list[Rating]})
    """

    ratings_history = rating_crud.fetch_history(
        db,
        rating_history.user,
        date(2001, 1, 1),
        fetch_variants,
    )
    _assert_correct_fetches(
        ratings_history,
        rating_history.variants,
        fetch_variants,
    )

    for fetched_ratings in ratings_history.values():
        for index, rating in enumerate(fetched_ratings):
            assert rating.elo == rating_history.elos[index]


@pytest.mark.integration
@pytest.mark.parametrize(
    "rating_history",
    [
        [enums.Variant.ANARCHY],
        enums.Variant,
        [],
    ],
    indirect=True,
)
def test_fetch_single(db: Session, rating_history: RatingHistory):
    variant = enums.Variant.ANARCHY

    fetched = rating_crud.fetch_single(
        db,
        user=rating_history.user,
        variant=variant,
    )

    if variant in rating_history.variants:
        assert fetched
        assert fetched.variant == variant
        assert fetched.is_active
    else:
        assert not fetched
