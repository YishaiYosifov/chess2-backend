from dataclasses import dataclass

from _pytest.fixtures import SubRequest
import pytest

from tests.factories.rating import RatingFactory
from app.models.user_model import User
from tests.factories.user import UserFactory
from app.constants import enums


@dataclass(frozen=True)
class RatingBatch:
    user: User
    variants: list[enums.Variant]


@dataclass(frozen=True)
class RatingHistory(RatingBatch):
    elos: list[int]


@pytest.fixture
def rating_batch(db, request: SubRequest) -> RatingBatch:
    variants: list[enums.Variant] = request.param

    user: User = UserFactory.create()
    RatingFactory.create_variant_batch(user, variants)

    return RatingBatch(user=user, variants=variants)


@pytest.fixture
def rating_history(db, request: SubRequest) -> RatingHistory:
    variants: list[enums.Variant] = request.param

    elos = [500, 57, 1]
    user: User = UserFactory.create()
    RatingFactory.create_history(user, {variant: elos for variant in variants})

    return RatingHistory(user=user, elos=elos, variants=variants)
