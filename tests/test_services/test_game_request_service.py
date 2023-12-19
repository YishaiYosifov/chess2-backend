from unittest.mock import MagicMock
from typing import Any

from pytest_mock.plugin import MockType
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from sqlalchemy import select
import pytest

from app.models.games.game_request_model import GameRequest
from app.models.games.game_model import Game
from tests.factories.user import AuthedUserFactory
from tests.factories.game import GameSettingsFactory, GameRequestFactory
from app.constants import constants, enums
from app.services import game_request_service
from app.schemas import game_schema
from app.crud import game_request_crud, rating_crud


@pytest.fixture
def mock_fetch_rating(mocker: MockerFixture):
    return mocker.patch.object(
        rating_crud,
        "fetch_single",
        return_value=mocker.Mock(elo=constants.DEFAULT_RATING),
    )


@pytest.fixture
def mock_search_request(mocker: MockerFixture):
    return mocker.patch.object(
        game_request_crud, "search_game_request", return_value=None
    )


@pytest.fixture
def mock_start_request(mocker: MockerFixture):
    return mocker.patch.object(
        game_request_service,
        "start_game_request",
        return_value=mocker.Mock(token="mocked token"),
    )


@pytest.fixture
def mock_create_request(mocker: MockerFixture):
    return mocker.patch.object(game_request_crud, "create_game_request")


@pytest.mark.unit
@pytest.mark.parametrize(
    "search_request_result, success",
    (
        (MagicMock(), True),
        (None, False),
    ),
    ids=["game request found", "game request missing"],
)
def test_create_or_start_pool_game(
    mocker: MockerFixture,
    mock_start_request: MockType,
    mock_search_request: MockType,
    mock_create_request: MockType,
    mock_fetch_rating: MockType,
    search_request_result: Any,
    success: bool,
):
    """
    Test the `create_or_start_pool_game` with both possibilities:
    - a game request was found, thus it should start the game
    - a game request was not found, thus it should create a game request
    """

    # Mock dependencies
    mock_search_request.return_value = search_request_result

    db = mocker.MagicMock()
    user = mocker.MagicMock()
    game_settings: game_schema.GameSettings = GameSettingsFactory.stub()
    results = game_request_service.create_or_start_pool_game(
        db, user, game_settings
    )
    assert results == (
        mock_start_request.return_value.token if success else None
    )

    # Assert everything was called correctly
    mock_fetch_rating.assert_called_once_with(
        db,
        user,
        variant=game_settings.variant,
    )

    mock_search_request.assert_called_once_with(
        db,
        game_settings,
        mock_fetch_rating.return_value.elo,
    )

    if success:
        mock_start_request.assert_called_once_with(
            db, search_request_result, user
        )
        mock_create_request.assert_not_called()
    else:
        mock_create_request.assert_called_once_with(db, user, game_settings)
        mock_start_request.assert_not_called()


class TestStartGameRequest:
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "last_color", (enums.Color.WHITE, enums.Color.BLACK)
    )
    def test_with_recipient(self, db: Session, last_color: enums.Color):
        """Test that `start_game_request` correctly creates the necessary entries and deletes the request"""

        inviter = AuthedUserFactory.create(last_color=last_color)
        game_request: GameRequest = GameRequestFactory.create(
            recipient=None, inviter=inviter
        )
        db.flush()

        inviter = game_request.inviter
        recipient = AuthedUserFactory.create()

        game = game_request_service.start_game_request(
            db, game_request, recipient
        )

        assert db.execute(select(Game)).scalar_one() == game
        assert not db.execute(select(GameRequest)).scalar()

        if last_color == enums.Color.WHITE:
            assert game.player_white.user == recipient
            assert game.player_black.user == inviter
        else:
            assert game.player_white.user == inviter
            assert game.player_black.user == recipient

    @pytest.mark.unit
    def test_without_recipient(self, db: Session):
        """Test that `start_game_request` raises a value error when a recipient is not provided"""

        game_request = GameRequestFactory.build(recipient=None)
        with pytest.raises(ValueError, match="Recipient not provided"):
            game_request_service.start_game_request(db, game_request)
