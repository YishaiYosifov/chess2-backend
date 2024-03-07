from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import UniqueConstraint, ForeignKey

from app.constants import enums
from app.db import Base

if TYPE_CHECKING:
    from app.models.games.live_game_model import LiveGame


class GamePiece(Base, kw_only=True):
    """Represents a piece in a game. This class holds its position, name and color."""

    __tablename__ = "game_piece"

    piece_id: Mapped[int] = mapped_column(primary_key=True, default=None)
    piece_type: Mapped[enums.PieceType]
    color: Mapped[enums.Color]

    times_moved: Mapped[int] = mapped_column(default=0)
    x: Mapped[int]
    y: Mapped[int]

    game_id: Mapped[int] = mapped_column(
        ForeignKey("live_game.live_game_id"),
        init=False,
        index=True,
    )
    game: Mapped[LiveGame] = relationship(back_populates="pieces")

    __table_args__ = (
        UniqueConstraint(x, y, game_id, name="unique_piece_position"),
    )
