from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import func, ForeignKey, Text

from app.constants import enums
from app.db import Base

if TYPE_CHECKING:
    from app.models.games.game_model import Game
    from app.models.user_model import AuthedUser


class RuntimePlayerInfo(Base, kw_only=True):
    """Stores user specifc information for an active game"""

    __tablename__ = "runtime_players_info"

    player_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("guest_users.user_id"),
        init=False,
    )
    user: Mapped[AuthedUser] = relationship(back_populates="player")

    game_white: Mapped[Game] = relationship(
        back_populates="player_white",
        foreign_keys="Game.player_white_id",
        init=False,
    )

    game_black: Mapped[Game] = relationship(
        back_populates="player_black",
        foreign_keys="Game.player_black_id",
        init=False,
    )

    @property
    def game(self) -> Game:
        return self.game_white or self.game_black

    sid: Mapped[str | None] = mapped_column(Text, default=None, nullable=True)
    color: Mapped[enums.Color]

    player_last_moved: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(),
        init=False,
    )
    time_remaining: Mapped[float]
