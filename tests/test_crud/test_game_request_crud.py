from datetime import timedelta, datetime
from typing import NamedTuple

from _pytest.fixtures import SubRequest
from sqlalchemy.orm import Session
import pytest

from app.models.games.game_request_model import GameRequest
from app.schemas.config_schema import CONFIG
from tests.factories.rating import RatingFactory
from app.models.user_model import AuthedUser
from tests.factories.user import AuthedUserFactory
from tests.factories.game import GameSettingsFactory, GameRequestFactory
from app.constants import enums
from app.schemas import game_schema
from app.crud import game_request_crud, rating_crud


def assert_game_request(
    db: Session,
    game_request: GameRequest | None,
    game_settings: game_schema.GameSettings,
    inviter: AuthedUser,
    rating: int | None = None,
):
    """
    Asserts that a game request matches specified conditions

    :param db: the database session
    :param game_request: the game request to be validated
    :param game_settings: the game settings the request is supposed to match
    :param inviter: the user who initiated the request
    :param rating: optional rating to check
    """

    assert game_request, f"Game request is {game_request}"

    assert (
        game_request.variant == game_settings.variant
    ), f"Mismatch variant: {game_request.variant} vs {game_settings.variant}"

    assert (
        game_request.time_control == game_settings.time_control
    ), f"Mismatch time control: {game_request.time_control} vs {game_settings.time_control}"

    assert (
        game_request.increment == game_settings.increment
    ), f"Mismatch increment: {game_request.increment} vs {game_settings.increment}"

    assert (
        game_request.inviter == inviter
    ), f"Mismatch inviter: {game_request.inviter.user_id} vs {inviter.user_id}"

    if not rating:
        return

    user_rating = rating_crud.fetch_single(db, inviter, game_settings.variant)
    if user_rating:
        assert user_rating.elo in range(
            rating - CONFIG.acceptable_rating_difference,
            rating + CONFIG.acceptable_rating_difference,
        ), f"Rating not in range: {user_rating.elo}"


class GameRequestData(NamedTuple):
    request: GameRequest
    settings: game_schema.GameSettings


@pytest.mark.integration
class TestSearchGameRequest:
    @pytest.fixture
    def game_request_data(
        self, db: Session, request: SubRequest
    ) -> GameRequestData:
        """
        Create a game request with the provided settings.
        Returns a named tuple with the given parametrized settings and the created request.
        """

        override_settings = getattr(request, "param", {})
        game_settings: game_schema.GameSettings = GameSettingsFactory.build(
            **override_settings
        )
        return GameRequestData(
            request=GameRequestFactory.create(game_settings=game_settings),
            settings=game_settings,
        )

    @pytest.fixture
    def game_settings(self, request: SubRequest) -> game_schema.GameSettings:
        """
        Create a basic game settings model.
        Default settings can be overriden with parametrize
        """

        override_settings = getattr(request, "param", {})
        return GameSettingsFactory.build(**override_settings)

    def test_success(self, db: Session, game_request_data: GameRequestData):
        """
        Test if `search_game_request` works with everything lining up correctly
        (no rating requirement and same settings).
        """

        request = game_request_data.request
        settings = game_request_data.settings

        fetched_request = game_request_crud.search_game_request(db, settings)
        assert_game_request(db, fetched_request, settings, request.inviter)

    @pytest.mark.parametrize(
        "game_request_data, fetch_settings",
        [
            (
                {"variant": enums.Variant.ANARCHY},
                {"variant": enums.Variant.CHSS},
            ),
            ({"time_control": 60}, {"time_control": 70}),
            ({"increment": 1}, {"increment": 0}),
        ],
        indirect=["game_request_data"],
    )
    def test_mismatch_settings(
        self,
        db: Session,
        game_request_data: GameRequestData,
        fetch_settings: dict,
    ):
        """Test if `search_game_request` correctly rejects game requests that do not have the right settings"""

        assert game_request_data.request
        assert not game_request_crud.search_game_request(
            db, GameSettingsFactory.build(**fetch_settings)
        )

    @pytest.mark.parametrize(
        "inviter_elo, fetch_elo, success",
        [
            (1100, 1200, True),
            (1300, 1200, True),
            (1501, 1200, False),
            (800, 1200, False),
        ],
    )
    def test_rating_range(
        self,
        db: Session,
        game_request_data: GameRequestData,
        inviter_elo: int,
        fetch_elo: int,
        success: bool,
    ):
        """Test if `search_game_request` correctly rejects / accepts game requests with elos in or out of acceptable range"""

        RatingFactory.create(
            user=game_request_data.request.inviter, elo=inviter_elo
        )
        fetched_request = game_request_crud.search_game_request(
            db, game_request_data.settings, fetch_elo
        )
        assert fetched_request if success else not fetched_request

    @pytest.mark.parametrize(
        "fetch_elo, success",
        [
            (CONFIG.default_rating, True),
            (CONFIG.default_rating - 50, True),
            (CONFIG.default_rating + 50, True),
            (CONFIG.default_rating - 350, False),
            (CONFIG.default_rating + 350, False),
        ],
    )
    def test_no_rating(
        self,
        db: Session,
        game_request_data: GameRequestData,
        fetch_elo: int,
        success: bool,
    ):
        """Test if `search_game_request` correctly uses the default rating if the inviting user doesn't have a rating"""

        fetched_request = game_request_crud.search_game_request(
            db, game_request_data.settings, fetch_elo
        )
        assert fetched_request if success else not fetched_request

    def test_multiple_matches(
        self, db: Session, game_settings: game_schema.GameSettings
    ):
        """Test if `search_game_request` correctly returns the oldest entry"""

        now = datetime.now()
        old = GameRequestFactory.create(
            game_settings=game_settings,
            created_at=now - timedelta(days=1),
        )
        # new
        GameRequestFactory.create(
            game_settings=game_settings,
            created_at=now,
        )

        fetched_request = game_request_crud.search_game_request(
            db, game_settings
        )
        assert fetched_request == old

    def test_request_with_recipient(
        self, db: Session, game_settings: game_schema.GameSettings
    ):
        """Test if `search_game_request` correctly ignores game requests with a recipient"""

        recipient = AuthedUserFactory.create()
        GameRequestFactory.create(
            game_settings=game_settings, recipient=recipient
        )

        assert not game_request_crud.search_game_request(db, game_settings)
