from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import func, CheckConstraint, ForeignKey, CHAR

from app.models.games.runtime_player_info_model import RuntimePlayerInfo
from app.models.games.piece_model import Piece
from app.constants import enums
from app.db import Base


class Game(Base, kw_only=True):
    __tablename__ = "games"

    game_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    token: Mapped[str] = mapped_column(CHAR(8))

    created_at: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(),
        init=False,
    )

    # Relationship to the white player
    player_white_id: Mapped[int] = mapped_column(
        ForeignKey("runtime_players_info.player_id"),
        init=False,
        index=True,
    )
    player_white: Mapped[RuntimePlayerInfo] = relationship(
        back_populates="game_white",
        foreign_keys=player_white_id,
    )

    # Relationship to the black player
    player_black_id: Mapped[int] = mapped_column(
        ForeignKey("runtime_players_info.player_id"),
        init=False,
        index=True,
    )
    player_black: Mapped[RuntimePlayerInfo] = relationship(
        back_populates="game_black",
        foreign_keys=player_black_id,
    )

    turn_player_id: Mapped[int] = mapped_column(
        ForeignKey("runtime_players_info.player_id"),
        insert_default=lambda context: context.get_current_parameters()[
            "player_white_id"
        ],
        init=False,
        index=True,
    )

    pieces: Mapped[list[Piece]] = relationship(
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
