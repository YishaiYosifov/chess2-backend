from datetime import datetime

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import func, CheckConstraint, ForeignKey, DateTime, CHAR

from app.models.games.live_player_model import LivePlayer
from app.models.games.game_piece_model import GamePiece
from app.constants import enums
from app.db import Base


class LiveGame(Base, kw_only=True):
    __tablename__ = "live_game"

    live_game_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    token: Mapped[str] = mapped_column(CHAR(8))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.current_timestamp(),
        init=False,
    )

    # Relationship to the white player
    player_white_id: Mapped[int] = mapped_column(
        ForeignKey("live_player.player_id"),
        init=False,
        index=True,
    )
    player_white: Mapped[LivePlayer] = relationship(
        back_populates="game_white",
        foreign_keys=player_white_id,
    )

    # Relationship to the black player
    player_black_id: Mapped[int] = mapped_column(
        ForeignKey("live_player.player_id"),
        init=False,
        index=True,
    )
    player_black: Mapped[LivePlayer] = relationship(
        back_populates="game_black",
        foreign_keys=player_black_id,
    )

    turn_player_id: Mapped[int] = mapped_column(
        ForeignKey("live_player.player_id"),
        insert_default=lambda context: context.get_current_parameters()[
            "player_white_id"
        ],
        init=False,
        index=True,
    )

    pieces: Mapped[list[GamePiece]] = relationship(
        back_populates="game",
        init=False,
    )

    variant: Mapped[enums.Variant]
    time_control: Mapped[int]
    increment: Mapped[int]

    __mapper_args__ = {
        "polymorphic_on": "variant",
        "polymorphic_identity": enums.Variant.ANARCHY,
    }

    __table_args__ = (
        CheckConstraint(
            "player_white_id <> player_black_id",
            name="different_players_constrain",
        ),
    )
