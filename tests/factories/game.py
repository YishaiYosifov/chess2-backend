from factory.alchemy import SQLAlchemyModelFactory
from factory import SubFactory, Faker

from app.models.games.game_request_model import GameRequest
from app.models.games.game_model import Game
from tests.factories.user import RuntimePlayerInfoFactory, UserFactory
from tests.conftest import ScopedSession
from app.constants import enums


class GameFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = ScopedSession
        model = Game

    token = Faker("pystr", max_chars=8)

    variant = enums.Variants.ANARCHY
    time_control = 600
    increment = 0

    player_white = SubFactory(RuntimePlayerInfoFactory)
    player_black = SubFactory(RuntimePlayerInfoFactory)


class GameRequestFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = ScopedSession
        model = GameRequest

    inviter = SubFactory(UserFactory, rating_variants=[enums.Variants.ANARCHY])

    variant = enums.Variants.ANARCHY
    time_control = 600
    increment = 0
