from typing import Sequence
import random
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.games.live_player_model import LivePlayer
from app.models.games.game_result_model import GameResult
from app.models.games.game_piece_model import GamePiece
from app.models.games.live_game_model import LiveGame
from app.models.user_model import AuthedUser, User
from app.constants import constants, enums


def paginate_history(
    db: Session,
    user: AuthedUser,
    page: int = 0,
    per_page: int = 10,
) -> Sequence[GameResult]:
    """
    Pageinate through game history for a specific page

    :param db: the database session
    :param user: the user to fetch the history of
    :param page: which page to fetch
    :param per_page: how many games to show per page

    :return: a list of games
    """

    games = (
        db.execute(
            select(GameResult)
            .filter(
                (GameResult.user_white == user)
                | (GameResult.user_black == user)
            )
            .order_by(GameResult.created_at.desc())
            .slice(page * per_page, page * per_page + per_page)
        )
        .scalars()
        .all()
    )

    return games


def total_count(db: Session, user: AuthedUser) -> int:
    """
    Count the total number of games the user has played

    :param db: the database session
    :param user: the user to check for
    """

    total = db.execute(
        select(func.count(GameResult.game_result_id)).filter(
            (GameResult.user_white == user) | (GameResult.user_black == user)
        )
    ).scalar()
    return total or 0


def create_players(
    db: Session, inviter: User, recipient: User, time_control: int
) -> tuple[LivePlayer, LivePlayer]:
    """
    Create the players for a game.
    Their colors will be decided by the inviter last color.

    :param db: the database session
    :param inviter: the player that started the request
    :param recipient: the player that is receiving the request
    :param time_control: the game time control to decide how much time each player has left
    """

    inviter_color = random.choice(list(enums.Color))
    recipient_color = inviter_color.invert()

    inviter_player = LivePlayer(
        user=inviter,
        color=inviter_color,
        time_remaining=time_control,
    )

    recipient_player = LivePlayer(
        user=recipient,
        color=recipient_color,
        time_remaining=time_control,
    )

    db.add_all([inviter_player, recipient_player])
    return inviter_player, recipient_player


def create_pieces(db: Session, game: LiveGame) -> None:
    """
    Create an entry for each piece in the starting position of game

    :param db: the database session
    :param game: the game to create the pieces for
    """

    # TODO: allow custom positions

    # fmt: off
    pieces = [
        GamePiece(**piece.model_dump(), game=game)
        for piece in constants.STARTING_POSITION
    ]
    # fmt: on
    db.add_all(pieces)


def create_game(
    db: Session,
    player1: LivePlayer,
    player2: LivePlayer,
    variant: enums.Variant,
    time_control: int,
    increment: int,
) -> LiveGame:
    game = LiveGame(
        token=uuid.uuid4().hex[:8],
        variant=variant,
        time_control=time_control,
        increment=increment,
        **{
            f"player_{player1.color.value}": player1,
            f"player_{player2.color.value}": player2,
        },
    )
    db.add(game)
    return game


def fetch_live_game(db: Session, token: str) -> LiveGame | None:
    """
    Fetch a live game by token

    :param db: the database session
    :param token: the game token to fetch

    :return: a game, or None if the game was not found
    """

    return db.execute(select(LiveGame).filter_by(token=token)).scalar()
