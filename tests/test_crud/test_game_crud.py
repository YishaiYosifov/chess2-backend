from typing import NamedTuple

from _pytest.fixtures import SubRequest
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from sqlalchemy import select
import pytest

from app.models.games.runtime_player_info_model import RuntimePlayerInfo
from app.models.games.game_results_model import GameResult
from app.models.games.piece_model import Piece
from app.models.user_model import AuthedUser
from tests.factories.user import AuthedUserFactory, PlayerFactory
from tests.factories.game import GameResultFactory, GameFactory
from app.constants import enums
from app.schemas import game_schema
from app.crud import game_crud


class GameHistory(NamedTuple):
    user1: AuthedUser
    user2: AuthedUser
    games: list[GameResult]


@pytest.fixture
def game_history(db, request: SubRequest) -> GameHistory:
    num_of_games: int = request.param

    user1 = AuthedUserFactory.create()
    user2 = AuthedUserFactory.create()
    games = GameResultFactory.create_history_batch(
        num_of_games,
        user1=user1,
        user2=user2,
    )

    return GameHistory(user1=user1, user2=user2, games=games)


@pytest.mark.integration
@pytest.mark.parametrize("game_history", (0, 3), indirect=["game_history"])
def test_total(db: Session, game_history: GameHistory):
    assert game_crud.total_count(db, game_history.user1) == len(
        game_history.games
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    "page, per_page, game_history",
    [(0, 2, 3), (1, 2, 5), (0, 2, 1), (0, 2, 0)],
    indirect=["game_history"],
)
def test_paginate_history(
    db: Session,
    page: int,
    per_page: int,
    game_history: GameHistory,
):
    """
    Test the `paginate_history` crud function with
    different page and per_page values and different game history sizes
    """

    fetched_history = game_crud.paginate_history(
        db,
        game_history.user1,
        page=page,
        per_page=per_page,
    )
    expected_games = game_history.games[
        per_page * page : per_page * page + per_page
    ]

    assert len(fetched_history) == len(expected_games)
    assert all(
        existing_game.game_results_id == fetched_game.game_results_id
        for existing_game, fetched_game in zip(
            expected_games,
            fetched_history,
        )
    ), len(game_history.games)


@pytest.mark.integration
@pytest.mark.parametrize(
    "inviter_color, recipient_color, expected_inviter_player_color",
    (
        [
            enums.Color.WHITE,
            enums.Color.BLACK,
            enums.Color.BLACK,
        ],
        [
            enums.Color.BLACK,
            enums.Color.BLACK,
            enums.Color.WHITE,
        ],
    ),
)
def test_create_players(
    db: Session,
    inviter_color: enums.Color,
    recipient_color: enums.Color,
    expected_inviter_player_color: enums.Color,
):
    """
    Test the `create_players` crud function to ensure it correctly assigns the colors
    the to inviter and recipient, as well as how much time they have remaining.
    """

    inviter = AuthedUserFactory.build(last_color=inviter_color)
    recipient = AuthedUserFactory.build(last_color=recipient_color)
    time_control = 69

    inviter_player, recipient_player = game_crud.create_players(
        db, inviter, recipient, time_control=time_control
    )

    assert len(db.execute(select(RuntimePlayerInfo)).all()) == 2
    assert (
        inviter_player.time_remaining
        == recipient_player.time_remaining
        == time_control
    )

    assert inviter_player.user == inviter
    assert recipient_player.user == recipient

    assert inviter_player.color == expected_inviter_player_color
    assert recipient_player.color == expected_inviter_player_color.invert()


@pytest.mark.integration
def test_create_pieces(db: Session, mocker: MockerFixture):
    """
    Test if the `create_pieces` function successfully creates all the pieces from the pieces constant
    in the correct order and with the correct parameters
    """

    starting_position = [
        game_schema.Piece(
            piece=enums.Piece.ROOK, color=enums.Color.WHITE, index=0
        ),
        game_schema.Piece(
            piece=enums.Piece.QUEEN, color=enums.Color.WHITE, index=10
        ),
        game_schema.Piece(
            piece=enums.Piece.PAWN, color=enums.Color.BLACK, index=15
        ),
        game_schema.Piece(
            piece=enums.Piece.HORSE, color=enums.Color.BLACK, index=20
        ),
    ]
    mocker.patch.object(
        game_crud.constants,
        "STARTING_POSITION",
        new=starting_position,
    )

    game = GameFactory.create()
    game_crud.create_pieces(db, game)

    created_pieces = db.execute(select(Piece)).scalars().all()

    assert len(created_pieces) == len(starting_position)
    for piece, expected_piece_data in zip(created_pieces, starting_position):
        assert piece.index == expected_piece_data.index
        assert piece.color == expected_piece_data.color
        assert piece.piece == expected_piece_data.piece


@pytest.mark.integration
def test_create_game(db: Session, mocker: MockerFixture):
    """
    Test if the `create_game` crud function correctly assigns the players to the correct color,
    the correct game settings and correct creates a token
    """

    uuid_hex = "0ef0f9722c0344ee94545bdca0613974"
    mocker.patch.object(
        game_crud.uuid, "uuid4", return_value=mocker.Mock(hex=uuid_hex)
    )

    player_white = PlayerFactory.create(color=enums.Color.WHITE)
    player_black = PlayerFactory.create(color=enums.Color.BLACK)
    variant = enums.Variant.ANARCHY
    time_control = 420
    increment = 69

    game = game_crud.create_game(
        db,
        player_white,
        player_black,
        variant=variant,
        time_control=time_control,
        increment=increment,
    )

    # assert db.execute(select(Game)).scalar_one() == game
    assert game.variant == variant
    assert game.time_control == time_control
    assert game.increment == increment
    assert game.player_white == player_white
    assert game.player_black == player_black
    assert game.token == uuid_hex[:8]
