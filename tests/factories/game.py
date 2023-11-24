from datetime import timedelta, datetime
from typing import Any

from factory.alchemy import SQLAlchemyModelFactory
from factory import SubFactory, Sequence, Faker

from app.models.games.game_results_model import GameResult
from app.models.games.game_request_model import GameRequest
from app.models.games.game_model import Game
from app.models.user_model import User
from tests.factories.user import RuntimePlayerInfoFactory, UserFactory
from tests.conftest import TestScopedSession
from app.constants import enums


class GameFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = Game

    game_id = Sequence(lambda n: n)
    token = Faker("pystr", max_chars=8)

    variant = enums.Variant.ANARCHY
    time_control = 600
    increment = 0

    player_white = SubFactory(RuntimePlayerInfoFactory)
    player_black = SubFactory(RuntimePlayerInfoFactory)


class GameRequestFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = GameRequest

    game_request_id = Sequence(lambda n: n)
    inviter = SubFactory(UserFactory)

    variant = enums.Variant.ANARCHY
    time_control = 600
    increment = 0


class GameResultFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = TestScopedSession
        model = GameResult

    game_results_id = Sequence(lambda n: n)
    token = Faker("pystr", max_chars=8)

    user_white = SubFactory(UserFactory)
    user_black = SubFactory(UserFactory)

    variant = enums.Variant.ANARCHY
    time_control = 600
    increment = 0

    results = enums.GameResult.WHITE

    created_at = Faker("date_time")

    @classmethod
    def create_history_batch(
        cls,
        size: int,
        user1: User,
        user2: User,
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
