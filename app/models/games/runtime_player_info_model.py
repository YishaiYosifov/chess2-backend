from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import func, ForeignKey, DateTime

from app.constants import enums
from app.db import Base

if TYPE_CHECKING:
    from app.models.games.live_game_model import LiveGame
    from app.models.user_model import User


class RuntimePlayerInfo(Base, kw_only=True):
    """Stores user specifc information for an active game"""

    __tablename__ = "runtime_player_info"

    player_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id"),
        init=False,
    )
    user: Mapped[User] = relationship(back_populates="player")

    game_white: Mapped[LiveGame] = relationship(
        back_populates="player_white",
        foreign_keys="LiveGame.player_white_id",
        init=False,
    )

    game_black: Mapped[LiveGame] = relationship(
        back_populates="player_black",
        foreign_keys="LiveGame.player_black_id",
        init=False,
    )

    @property
    def game(self) -> LiveGame:
        return self.game_white or self.game_black

    color: Mapped[enums.Color]

    player_last_moved: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.current_timestamp(),
        init=False,
    )
    time_remaining: Mapped[float]
