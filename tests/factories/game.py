from datetime import timedelta, datetime
from typing import Any

import factory

from app.models.games.game_request_model import GameRequest
from app.models.games.game_result_model import GameResult
from app.models.games.live_game_model import LiveGame
from tests.utils.factory_model import TypedSQLAlchemyFactory, TypedFactory
from app.models.user_model import AuthedUser
from tests.factories.user import AuthedUserFactory, PlayerFactory
from tests.conftest import TestScopedSession
from app.schemas import game_schema
from app.types import PieceInfo
from app import enums


class LiveGameFactory(TypedSQLAlchemyFactory[LiveGame]):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = LiveGame

    token = factory.Faker("pystr", max_chars=8)

    fen = "rhnxqkbahr/ddpdppdpdd/c8c/10/10/10/10/C8C/DDPDPPDPDD/RHNXQKBAHR"

    variant = enums.Variant.ANARCHY
    time_control = 600
    increment = 0

    player_white = factory.SubFactory(PlayerFactory)
    player_black = factory.SubFactory(PlayerFactory)


class PieceInfoFactory(TypedFactory[PieceInfo]):
    class Meta:
        model = PieceInfo

    piece_type = enums.PieceType.PAWN
    color = enums.Color.WHITE


class GameResultFactory(TypedSQLAlchemyFactory[GameResult]):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = GameResult

    token = factory.Faker("pystr", max_chars=8)

    user_white = factory.SubFactory(AuthedUserFactory)
    user_black = factory.SubFactory(AuthedUserFactory)

    variant = enums.Variant.ANARCHY
    time_control = 600
    increment = 0

    results = enums.GameResult.WHITE

    created_at = factory.Faker("date_time")

    @classmethod
    def create_history_batch(
        cls,
        size: int,
        user1: AuthedUser,
        user2: AuthedUser,
        created_at: datetime | None = None,
        **kwargs: Any
    ) -> list[GameResult]:
        """
        Create a history batch of games.
        In this batch, user1 and user 2 will alternate between user_white and user_black.
        The create_at date will also decrease by 1 day for each game

        :param size: how many games to create
        :param user1: the first user
        :param user2: the second user
        :param created_at: optionally set the date of the first game. defaults to utcnow

        :return: a list of game results
        """

        created_at = created_at or datetime.utcnow()
        users = [user1, user2]

        games = []
        for _ in range(size):
            game = cls.create(
                created_at=created_at,
                user_white=users[0],
                user_black=users[1],
                **kwargs
            )
            games.append(game)

            # Prepare the next game
            created_at -= timedelta(days=1)
            users = users[::-1]

        return games


class GameRequestFactory(TypedSQLAlchemyFactory[GameRequest]):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = GameRequest

    inviter = factory.SubFactory(AuthedUserFactory)

    variant = enums.Variant.ANARCHY
    time_control = 600
    increment = 0

    @classmethod
    def create(cls, settings: game_schema.GameSettings | None = None, **kwargs):
        if settings:
            kwargs.update(settings.model_dump())

        return super().create(**kwargs)


class GameSettingsFactory(TypedFactory[game_schema.GameSettings]):
    class Meta:
        model = game_schema.GameSettings

    variant = enums.Variant.ANARCHY
    time_control = 600
    increment = 0
