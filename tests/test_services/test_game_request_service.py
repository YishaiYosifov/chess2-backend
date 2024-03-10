from unittest.mock import MagicMock
from typing import Any

from pytest_mock.plugin import MockType
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from sqlalchemy import select
import pytest

from app.models.games.game_request_model import GameRequest
from app.models.games.live_game_model import LiveGame
from app.models.user_model import User
from tests.factories.user import AuthedUserFactory, GuestUserFactory
from tests.factories.game import GameSettingsFactory, GameRequestFactory
from app.services import game_request_service
from app.crud import game_request_crud, rating_crud, game_crud
from app import enums


@pytest.mark.usefixtures(
    "mock_start_request",
    "mock_search_request",
    "mock_create_request",
    "mock_fetch_rating",
)
class TestCreateOrStartPoolGame:
    @pytest.fixture
    def mock_fetch_rating(self, mocker: MockerFixture):
        return mocker.patch.object(rating_crud, "fetch_rating_elo")

    @pytest.fixture
    def mock_search_request(self, mocker: MockerFixture):
        return mocker.patch.object(
            game_request_crud,
            "search_game_request",
            return_value=None,
        )

    @pytest.fixture
    def mock_start_request(self, mocker: MockerFixture):
        return mocker.patch.object(
            game_request_service,
            "start_game_request",
            return_value=mocker.Mock(token="mocked token"),
        )

    @pytest.fixture
    def mock_create_request(self, mocker: MockerFixture):
        return mocker.patch.object(game_request_crud, "create_game_request")

    @pytest.mark.unit
    def test_correct_rating_calls_authed(
        self,
        mocker: MockerFixture,
        mock_search_request: MockType,
        mock_fetch_rating: MockType,
    ):
        """
        Test if the correct rating is fetched when the user is authenticated.
        If the user doesn't have a rating in that specific variant, the default one
        should be used.
        """

        mock_fetch_rating.return_value = 800

        db = mocker.MagicMock()
        game_settings = GameSettingsFactory.build()
        user = AuthedUserFactory.build()
        game_request_service.create_or_start_pool_game(db, user, game_settings)

        mock_fetch_rating.assert_called_once_with(
            db, user, game_settings.variant
        )
        mock_search_request.assert_called_once_with(
            db, game_settings, 800, enums.UserType.AUTHED
        )

    @pytest.mark.unit
    def test_correct_ratings_unauthed(
        self,
        mocker: MockerFixture,
        mock_fetch_rating: MockType,
        mock_search_request: MockType,
    ):
        """Test that `None` is used as the rating if the user is not authenticated"""

        db = mocker.MagicMock()
        game_settings = GameSettingsFactory.build()
        user = GuestUserFactory.build()
        game_request_service.create_or_start_pool_game(db, user, game_settings)

        mock_fetch_rating.assert_not_called()
        mock_search_request.assert_called_once_with(
            db, game_settings, None, enums.UserType.GUEST
        )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "search_request_result",
        (MagicMock(), None),
        ids=["game request found", "game request missing"],
    )
    @pytest.mark.parametrize(
        "user",
        [AuthedUserFactory.build(), GuestUserFactory.build()],
        ids=["is authed", "is not authed"],
    )
    def test_correct_calls_for_game_request_existence(
        self,
        mocker: MockerFixture,
        user: User,
        mock_start_request: MockType,
        mock_create_request: MockType,
        mock_search_request: MockType,
        search_request_result: Any,
    ):
        """
        Test that it correctly either starts the game request
        or creates a game request depending on whether it found a game request.

        Tests for both authed and unauthed users.
        """

        mock_search_request.return_value = search_request_result

        db = mocker.MagicMock()
        game_settings = GameSettingsFactory.build()
        token = game_request_service.create_or_start_pool_game(
            db, user, game_settings
        )

        if search_request_result:
            assert token
            mock_start_request.assert_called_once_with(
                db, search_request_result, user
            )
            mock_create_request.assert_not_called()
        else:
            assert not token
            mock_create_request.assert_called_once_with(db, user, game_settings)
            mock_start_request.assert_not_called()


class TestStartGameRequest:
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "user_factory", [AuthedUserFactory, GuestUserFactory]
    )
    def test_with_recipient(
        self,
        db: Session,
        mocker: MockerFixture,
        user_factory: SQLAlchemyModelFactory,
    ):
        """Test that `start_game_request` correctly creates the necessary entries and deletes the request"""

        color = enums.Color.WHITE
        mocker.patch.object(
            game_crud.random,
            "choice",
            return_value=enums.Color.WHITE,
        )

        inviter = user_factory.create()
        game_request = GameRequestFactory.create(
            recipient=None, inviter=inviter
        )
        db.flush()

        inviter = game_request.inviter
        recipient = user_factory.create()

        game = game_request_service.start_game_request(
            db, game_request, recipient
        )

        assert db.execute(select(LiveGame)).scalar_one() == game
        assert not db.execute(select(GameRequest)).scalar()

        if color == enums.Color.WHITE:
            assert game.player_white.user == inviter
            assert game.player_black.user == recipient
        else:
            assert game.player_white.user == recipient
            assert game.player_black.user == inviter

    @pytest.mark.unit
    def test_without_recipient(self, db: Session):
        """Test that `start_game_request` raises a value error when a recipient is not provided"""

        game_request = GameRequestFactory.build(recipient=None)
        with pytest.raises(ValueError, match="Recipient not provided"):
            game_request_service.start_game_request(db, game_request)
