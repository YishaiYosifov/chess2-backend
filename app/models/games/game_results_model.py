from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import func, ForeignKey, CHAR

from app.constants import enums
from app.db import Base

if TYPE_CHECKING:
    from app.models.user_model import User


class GameResult(Base, kw_only=True):
    """Stores the results of a game after it ends"""

    __tablename__ = "game_results"

    game_results_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    token: Mapped[str] = mapped_column(CHAR(8))

    user_white_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    user_white: Mapped[User] = relationship(foreign_keys=user_white_id)

    user_black_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    user_black: Mapped[User] = relationship(foreign_keys=user_black_id)

    variant: Mapped[enums.Variants]
    time_control: Mapped[int]
    increment: Mapped[int]

    winner_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    winner: Mapped[User] = relationship(foreign_keys=winner_id)

    created_at: Mapped[datetime]
    ended_at: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(),
        init=False,
    )
