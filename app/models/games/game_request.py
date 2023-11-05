from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import func, ForeignKey

from app.enums import Variants
from app.db import Base

if TYPE_CHECKING:
    from app.models.user import User


class GameRequest(Base, kw_only=True):
    """
    Stores game requests.
    This includes the game pool (when the recipient is not specified) and invite requests
    (when a recipient is specified)
    """

    __tablename__ = "game_requests"

    game_request_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), init=False)
    inviter: Mapped[User] = relationship(
        foreign_keys=inviter_id,
        back_populates="game_request",
    )

    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=True, init=False
    )
    recipient: Mapped[User] = relationship(
        foreign_keys=recipient_id,
        back_populates="incoming_games",
        default=None,
    )

    variant: Mapped[Variants]
    time_control: Mapped[int]
    increment: Mapped[int]

    created_at: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(),
        init=False,
    )
