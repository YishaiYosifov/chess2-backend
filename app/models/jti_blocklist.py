from __future__ import annotations

from sqlalchemy.orm import mapped_column, Mapped

from app.db import Base


class JTIBlocklist(Base, kw_only=True):
    __tablename__ = "jti_blocklist"

    jti_id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(index=True)
