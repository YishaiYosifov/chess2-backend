from datetime import timedelta, datetime
from typing import Any

from factory.alchemy import SQLAlchemyModelFactory
from factory import SubFactory, Factory, Faker

from app.models.games.game_request_model import GameRequest
from app.models.games.game_result_model import GameResult
from app.models.games.game_model import Game
from app.models.user_model import AuthedUser
from tests.factories.user import AuthedUserFactory, PlayerFactory
from tests.conftest import TestScopedSession
from app.constants import enums
from app.schemas import game_schema


class GameFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = Game

    token = Faker("pystr", max_chars=8)

    variant = enums.Variant.ANARCHY
    time_control = 600
    increment = 0

    player_white = SubFactory(PlayerFactory)
    player_black = SubFactory(PlayerFactory)


class GameRequestFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = GameRequest

    inviter = SubFactory(AuthedUserFactory)

    variant = enums.Variant.ANARCHY
    time_control = 600
    increment = 0

    @classmethod
    def create(
        cls, game_settings: game_schema.GameSettings | None = None, **kwargs
    ):
        if game_settings:
            kwargs.update(game_settings.model_dump())

        return super().create(**kwargs)


class GameResultFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = GameResult

    token = Faker("pystr", max_chars=8)

    user_white = SubFactory(AuthedUserFactory)
    user_black = SubFactory(AuthedUserFactory)

    variant = enums.Variant.ANARCHY
    time_control = 600
    increment = 0

    results = enums.GameResult.WHITE

    created_at = Faker("date_time")

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


class GameSettingsFactory(Factory):
    class Meta:
        model = game_schema.GameSettings

    variant = enums.Variant.ANARCHY
    time_control = 60
    increment = 0
