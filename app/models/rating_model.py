from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import event, func, ForeignKey, Index, DDL

from app.constants import enums
from app.db import Base

if TYPE_CHECKING:
    from app.models.user_model import User


class Rating(Base, kw_only=True):
    """
    This table stores the rating information of each specific variant for a user.
    When this table is updated, it inserts a new row with the old values and is_active set to false.
    """

    __tablename__ = "ratings"

    rating_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), init=False)
    user: Mapped[User] = relationship(back_populates="ratings")

    variant: Mapped[enums.Variant] = mapped_column()
    elo: Mapped[int] = mapped_column(default=800)

    achieved_at: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(),
        default=None,
    )

    __table_args__ = (
        Index(
            "unique_active_user_variant",
            user_id,
            variant,
            is_active,
            unique=True,
            postgresql_where=is_active,
        ),
    )


# Automatically mark old ratings as non active when new ones are inserted
create_trigger_function = DDL(
    """
    CREATE OR REPLACE FUNCTION archive_ratings()
    RETURNS TRIGGER AS
    $BODY$
    BEGIN
        IF NEW.elo <> OLD.elo THEN
            INSERT INTO ratings (
                is_active,
                user_id,
                variant,
                elo,
                achieved_at
            ) VALUES (
                FALSE,
                OLD.user_id,
                OLD.variant,
                OLD.elo,
                OLD.achieved_at
            );
        END IF;
        RETURN NEW;
    END;
    $BODY$
    LANGUAGE PLPGSQL;
    """
)
event.listen(
    Rating.__table__,
    "after_create",
    create_trigger_function,
)

create_trigger = DDL(
    """
    CREATE OR REPLACE TRIGGER rating_archiver
    BEFORE UPDATE
    ON ratings
    FOR EACH ROW
        EXECUTE PROCEDURE archive_ratings();
    """
)
event.listen(
    Rating.__table__,
    "after_create",
    create_trigger,
)
