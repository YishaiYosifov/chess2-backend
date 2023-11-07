from factory import SubFactory, Faker

from app.models.games.game_request import GameRequest
from app.models.games.game import Game
from tests.factories.user import RuntimePlayerInfoFactory, UserFactory
from app.constants.enums import Variants
from tests.factories import BaseSQLAlchemyModelFactory


class GameFactory(BaseSQLAlchemyModelFactory[Game]):
    class Meta:
        model = Game

    token = Faker("pystr", max_chars=8)

    variant = Variants.ANARCHY
    time_control = 600
    increment = 0

    player_white = SubFactory(RuntimePlayerInfoFactory)
    player_black = SubFactory(RuntimePlayerInfoFactory)


class GameRequestFactory(BaseSQLAlchemyModelFactory[GameRequest]):
    class Meta:
        model = GameRequest

    inviter = SubFactory(UserFactory, rating_variants=[Variants.ANARCHY])

    variant = Variants.ANARCHY
    time_control = 600
    increment = 0
