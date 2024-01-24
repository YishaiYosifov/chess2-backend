import urllib.parse

from sqlalchemy.orm import sessionmaker, MappedAsDataclass, DeclarativeBase
from sqlalchemy import create_engine

from app.schemas.config_schema import CONFIG


class Base(MappedAsDataclass, DeclarativeBase):
    pass


engine = create_engine(
    "postgresql+psycopg2://"
    f"{CONFIG.postgres_user}:{urllib.parse.quote(CONFIG.postgres_password)}"
    f"@{CONFIG.postgres_host}/{CONFIG.postgres_db}",
    connect_args={"options": "-c timezone=UTC"},
)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)
