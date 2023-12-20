from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import func, ForeignKey, String, Text

from app.models.games.runtime_player_info_model import RuntimePlayerInfo
from app.models.games.game_request_model import GameRequest
from app.models.games.game_model import Game
from app.models.rating_model import Rating
from app.constants import enums
from app.db import Base


class GuestUser(Base, kw_only=True):
    __tablename__ = "guest_users"

    user_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    is_authed: Mapped[bool] = mapped_column(init=False)

    sid: Mapped[str | None] = mapped_column(
        Text,
        default=None,
        init=False,
        nullable=True,
        unique=True,
    )

    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    last_color: Mapped[enums.Color] = mapped_column(default=enums.Color.BLACK)

    created_at: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(),
        default=None,
    )

    game_request: Mapped[GameRequest | None] = relationship(
        back_populates="inviter",
        foreign_keys=GameRequest.inviter_id,
        init=False,
    )

    player: Mapped[RuntimePlayerInfo | None] = relationship(
        back_populates="user",
        default=None,
    )

    __mapper_args__ = {
        "polymorphic_identity": False,
        "polymorphic_on": is_authed,
    }

    def __eq__(self, to) -> bool:
        from .games.runtime_player_info_model import RuntimePlayerInfo

        if not isinstance(to, GuestUser) and not isinstance(
            to, RuntimePlayerInfo
        ):
            return False
        return to.user_id == self.user_id

    @property
    def game(self) -> Game | None:
        if not self.player:
            return

        return self.player.game


class AuthedUser(GuestUser):
    __tablename__ = "authed_users"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("guest_users.user_id"), primary_key=True, init=False
    )
    hashed_password: Mapped[str]

    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    is_email_verified: Mapped[bool] = mapped_column(default=False)

    about: Mapped[str] = mapped_column(String(300), default="")
    country: Mapped[str | None] = mapped_column(String(100), default=None)

    username_last_changed: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None,
    )
    pfp_last_changed: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(),
        default=None,
    )

    incoming_games: Mapped[list[GameRequest]] = relationship(
        back_populates="recipient",
        foreign_keys=GameRequest.recipient_id,
        init=False,
    )

    ratings: Mapped[list[Rating]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        init=False,
    )

    __mapper_args__ = {
        "polymorphic_identity": True,
    }
