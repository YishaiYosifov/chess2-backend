from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import func, String, Text

from app.models.games.runtime_player_info import RuntimePlayerInfo
from app.models.games.game_request import GameRequest
from app.models.games.game import Game
from app.models.rating import Rating
from app.enums import Colors
from app.db import Base


class User(Base, kw_only=True):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    sid: Mapped[str | None] = mapped_column(
        Text,
        default=None,
        init=False,
        nullable=True,
        unique=True,
    )
    hashed_password: Mapped[str] = mapped_column()

    username: Mapped[str] = mapped_column(String(30), unique=True)
    email: Mapped[str] = mapped_column(String(256), unique=True)
    about: Mapped[str] = mapped_column(String(300), default="")
    country: Mapped[str] = mapped_column(String(100), default="international")

    is_email_verified: Mapped[bool] = mapped_column(default=False)

    last_color: Mapped[Colors] = mapped_column(default=Colors.BLACK)

    email_last_changed: Mapped[datetime | None] = mapped_column(
        nullable=True, default=None
    )

    username_last_changed: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None,
    )
    pfp_last_changed: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(),
        default=None,
    )

    created_at: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(),
        default=None,
    )

    ratings: Mapped[list[Rating]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        init=False,
    )

    game_request: Mapped[GameRequest | None] = relationship(
        back_populates="inviter",
        foreign_keys=GameRequest.inviter_id,
        init=False,
    )

    incoming_games: Mapped[list[GameRequest]] = relationship(
        back_populates="recipient",
        foreign_keys=GameRequest.recipient_id,
        init=False,
    )

    player: Mapped[RuntimePlayerInfo | None] = relationship(
        back_populates="user",
        default=None,
    )

    def __eq__(self, to) -> bool:
        from .games.runtime_player_info import RuntimePlayerInfo

        if not isinstance(to, User) and not isinstance(to, RuntimePlayerInfo):
            return False
        return to.user_id == self.user_id

    @property
    def game(self) -> Game | None:
        if not self.player:
            return

        return self.player.game
