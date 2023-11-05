from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import UniqueConstraint, ForeignKey

from app.enums import Pieces, Colors
from app.db import Base

if TYPE_CHECKING:
    from app.models.games.game import Game


class PiecePosition(Base, kw_only=True):
    """Represents a piece in a game. This class holds its index (position), name and color."""

    __tablename__ = "piece_positions"

    piece_position_id: Mapped[int] = mapped_column(init=False, primary_key=True)
    piece: Mapped[Pieces]
    color: Mapped[Colors]

    index: Mapped[int] = mapped_column()

    game_id: Mapped[int] = mapped_column(ForeignKey("games.game_id"), init=False)
    game: Mapped[Game] = relationship(back_populates="pieces")

    __table_args__ = (UniqueConstraint(index, game_id, name="unique_piece_index"),)
