from datetime import timedelta

from sqlalchemy.orm import Session
import pytest

from app.schemas.config_schema import CONFIG
from tests.factories.rating import RatingFactory
from tests.factories.user import AuthedUserFactory, GuestUserFactory
from tests.factories.game import GameSettingsFactory, GameRequestFactory
from app.constants import enums
from tests.utils import mocks
from app.schemas import game_schema
from app.crud import game_request_crud


@pytest.mark.integration
class TestSearchGameRequest:
    def test_success(self, db: Session):
        """
        Test if it works with every condition met
        (no rating requirement and same settings)
        """

        settings = GameSettingsFactory.build()
        request = GameRequestFactory.create(settings)

        fetched_request = game_request_crud.search_game_request(db, settings)

        assert fetched_request == request

    @pytest.mark.parametrize(
        "create_settings, fetch_settings",
        [
            (
                GameSettingsFactory.build(variant=enums.Variant.ANARCHY),
                GameSettingsFactory.build(variant=enums.Variant.CHSS),
            ),
            (
                GameSettingsFactory.build(time_control=60),
                GameSettingsFactory.build(time_control=70),
            ),
            (
                GameSettingsFactory.build(increment=0),
                GameSettingsFactory.build(time_control=1),
            ),
        ],
    )
    def test_mismatch_settings(
        self,
        db: Session,
        create_settings: game_schema.GameSettings,
        fetch_settings: game_schema.GameSettings,
    ):
        """
        Test if it correctly rejects game requests that do not
        have the right settings
        """

        GameRequestFactory.create(create_settings)

        fetched_request = game_request_crud.search_game_request(
            db, fetch_settings
        )

        assert not fetched_request

    @pytest.mark.parametrize(
        "inviter_elo, fetch_elo, success",
        [
            (1100, 1200, True),
            (1300, 1200, True),
            (1501, 1200, False),
            (800, 1200, False),
            (None, CONFIG.default_rating, True),
            (None, CONFIG.default_rating - 50, True),
            (None, CONFIG.default_rating + 50, True),
            (None, CONFIG.default_rating - 350, False),
            (None, CONFIG.default_rating + 350, False),
        ],
    )
    def test_rating_range(
        self,
        db: Session,
        inviter_elo: int,
        fetch_elo: int,
        success: bool,
    ):
        """
        Test if it correctly rejects / accepts game requests with elos in or out of
        acceptable range. Also tests when the user doesn't have a rating.
        """

        settings = GameSettingsFactory.build()
        request = GameRequestFactory.create(settings)
        if inviter_elo:
            RatingFactory.create(user=request.inviter, elo=inviter_elo)

        fetched_request = game_request_crud.search_game_request(
            db, settings, fetch_elo
        )

        assert (fetched_request == request) if success else not fetched_request

    def test_multiple_matches(self, db: Session, mocker):
        """Test if it correctly returns the oldest entry"""

        settings = GameSettingsFactory.build()

        fixed_datetime, _ = mocks.fix_time(game_request_crud, mocker)
        old = GameRequestFactory.create(
            settings,
            created_at=fixed_datetime - timedelta(days=1),
        )
        GameRequestFactory.create(settings, created_at=fixed_datetime)

        fetched_request = game_request_crud.search_game_request(db, settings)
        assert fetched_request == old

    def test_with_recipient(self, db: Session):
        """Test if it correctly ignores game requests with a recipient"""

        settings = GameSettingsFactory.build()
        GameRequestFactory.create(
            settings, recipient=AuthedUserFactory.create()
        )

        fetched_request = game_request_crud.search_game_request(db, settings)
        assert not fetched_request

    @pytest.mark.parametrize(
        "user_type", [enums.UserType.AUTHED, enums.UserType.GUEST]
    )
    def test_authed_guest_mismatch(
        self,
        db: Session,
        user_type,
    ):
        """Test that an authed user can't match with a guest user and vice versa"""

        inviter = (
            AuthedUserFactory.create()
            if user_type == enums.UserType.GUEST
            else GuestUserFactory.create()
        )

        settings = GameSettingsFactory.build()
        GameRequestFactory.create(settings, inviter=inviter)

        fetched_request = game_request_crud.search_game_request(
            db, settings, user_type=user_type
        )

        assert not fetched_request
