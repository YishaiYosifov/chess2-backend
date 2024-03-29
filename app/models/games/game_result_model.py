from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import func, ForeignKey, DateTime, CHAR

from app.db import Base
from app import enums

if TYPE_CHECKING:
    from app.models.user_model import AuthedUser


class GameResult(Base, kw_only=True):
    """Stores the results of a game after it ends"""

    __tablename__ = "game_result"

    game_result_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    token: Mapped[str] = mapped_column(CHAR(8))

    user_white_id: Mapped[int] = mapped_column(
        ForeignKey("authed_user.user_id", ondelete="SET NULL"),
        nullable=True,
        init=False,
        index=True,
    )
    user_white: Mapped[AuthedUser] = relationship(foreign_keys=user_white_id)

    user_black_id: Mapped[int] = mapped_column(
        ForeignKey("authed_user.user_id", ondelete="SET NULL"),
        nullable=True,
        init=False,
        index=True,
    )
    user_black: Mapped[AuthedUser] = relationship(foreign_keys=user_black_id)

    variant: Mapped[enums.Variant]
    time_control: Mapped[int]
    increment: Mapped[int]

    results: Mapped[enums.GameResult]

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.current_timestamp(),
        init=False,
    )
