from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import func, ForeignKey, DateTime, String

from app.models.games.runtime_player_info_model import RuntimePlayerInfo
from app.models.games.game_request_model import GameRequest
from app.models.games.game_model import Game
from app.models.rating_model import Rating
from app.constants import enums
from app.db import Base


class User(Base, kw_only=True):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_type: Mapped[enums.UserType] = mapped_column(init=False)

    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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

    last_refreshed_token: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.current_timestamp(),
        default=None,
    )

    @property
    def game(self) -> Game | None:
        if not self.player:
            return

        return self.player.game

    __mapper_args__ = {
        "polymorphic_on": user_type,
        "polymorphic_abstract": True,
    }


class GuestUser(User, kw_only=True):
    __tablename__ = "guest_user"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id"),
        primary_key=True,
        init=False,
    )

    __mapper_args__ = {"polymorphic_identity": enums.UserType.GUEST}


class AuthedUser(User, kw_only=True):
    __tablename__ = "authed_user"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id"),
        primary_key=True,
        default=None,
    )
    hashed_password: Mapped[str]

    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    is_email_verified: Mapped[bool] = mapped_column(default=False)

    about: Mapped[str] = mapped_column(String(300), default="")
    country: Mapped[str | None] = mapped_column(String(64), default="INTR")

    username_last_changed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    pfp_last_changed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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

    __mapper_args__ = {"polymorphic_identity": enums.UserType.AUTHED}
