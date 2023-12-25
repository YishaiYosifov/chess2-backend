from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import UniqueConstraint, ForeignKey

from app.constants import enums
from app.db import Base

if TYPE_CHECKING:
    from app.models.games.game_model import Game


class Piece(Base, kw_only=True):
    """Represents a piece in a game. This class holds its index (position), name and color."""

    __tablename__ = "piece_position"

    piece_position_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    piece: Mapped[enums.Piece]
    color: Mapped[enums.Color]

    index: Mapped[int] = mapped_column()

    game_id: Mapped[int] = mapped_column(
        ForeignKey("game.game_id"),
        init=False,
        index=True,
    )
    game: Mapped[Game] = relationship(back_populates="pieces")

    __table_args__ = (
        UniqueConstraint(index, game_id, name="unique_piece_index"),
    )
