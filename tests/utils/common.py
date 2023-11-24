from collections import Counter
from typing import Any
import math


from app.models.games.game_model import Game
from app.models.user_model import User
from app.constants import enums


def get_duplicates(list: list[Any]):
    """Only get the duplicate items from a list"""

    counter = Counter(list)
    return [item for item, occurrences in counter.items() if occurrences >= 2]


def is_user_in_game(user: User, game: Game) -> bool:
    return (
        user.user_id == game.player_white.user_id
        if user.last_color == enums.Color.WHITE
        else user.user_id == game.player_black.user_id
    )


def page_count(total: int, per_page: int) -> int:
    return math.ceil((total or 0) / per_page)
