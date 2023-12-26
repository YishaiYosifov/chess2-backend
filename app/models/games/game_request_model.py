from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import func, ForeignKey, DateTime

from app.constants import enums
from app.db import Base

if TYPE_CHECKING:
    from app.models.user_model import AuthedUser


class GameRequest(Base, kw_only=True):
    """
    Stores game requests.
    This includes the game pool (when the recipient is not specified) and invite requests
    (when a recipient is specified)
    """

    __tablename__ = "game_request"

    game_request_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    inviter_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id"),
        init=False,
        index=True,
    )
    inviter: Mapped[AuthedUser] = relationship(
        foreign_keys=inviter_id,
        back_populates="game_request",
    )

    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id"),
        nullable=True,
        init=False,
        index=True,
    )
    recipient: Mapped[AuthedUser] = relationship(
        foreign_keys=recipient_id,
        back_populates="incoming_games",
        default=None,
    )

    variant: Mapped[enums.Variant]
    time_control: Mapped[int]
    increment: Mapped[int]

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.current_timestamp(),
        default=None,
    )
