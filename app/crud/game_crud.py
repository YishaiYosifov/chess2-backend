from typing import Sequence
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.games.runtime_player_info_model import RuntimePlayerInfo
from app.models.games.game_results_model import GameResult
from app.models.games.piece_model import Piece
from app.models.games.game_model import Game
from app.models.user_model import AuthedUser
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
        select(func.count(GameResult.game_results_id)).filter(
            (GameResult.user_white == user) | (GameResult.user_black == user)
        )
    ).scalar()
    return total or 0


def create_players(
    db: Session, inviter: AuthedUser, recipient: AuthedUser, time_control: int
) -> tuple[RuntimePlayerInfo, RuntimePlayerInfo]:
    """
    Create the players for a game.
    Their colors will be decided by the inviter last color.

    :param db: the database session
    :param inviter: the player that started the request
    :param recipient: the player that is receiving the request
    :param time_control: the game time control to decide how much time each player has left
    """

    inviter_color = inviter.last_color.invert()
    recipient_color = inviter.last_color

    inviter_player = RuntimePlayerInfo(
        user=inviter,
        color=inviter_color,
        time_remaining=time_control,
    )
    inviter.last_color = inviter_color

    recipient_player = RuntimePlayerInfo(
        user=recipient,
        color=recipient_color,
        time_remaining=time_control,
    )
    recipient.last_color = recipient_color

    db.add_all([inviter_player, recipient_player])
    return inviter_player, recipient_player


def create_pieces(db: Session, game: Game):
    """
    Create an entry for each piece in the starting position of game

    :param db: the database session
    :param game: the game to create the pieces for
    """

    # TODO: allow custom positions

    # fmt: off
    pieces = [
        Piece(**piece.model_dump(), game=game)
        for piece in constants.STARTING_POSITION
    ]
    # fmt: on
    db.add_all(pieces)


def create_game(
    db: Session,
    player1: RuntimePlayerInfo,
    player2: RuntimePlayerInfo,
    variant: enums.Variant,
    time_control: int,
    increment: int,
) -> Game:
    game = Game(
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
