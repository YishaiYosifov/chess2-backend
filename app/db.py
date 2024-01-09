import urllib.parse

from sqlalchemy.orm import sessionmaker, MappedAsDataclass, DeclarativeBase
from sqlalchemy import create_engine

from app.schemas.config_schema import CONFIG


class Base(MappedAsDataclass, DeclarativeBase):
    pass


engine = create_engine(
    "postgresql+psycopg2://"
    f"{CONFIG.db_user}:{urllib.parse.quote(CONFIG.db_password)}"
    f"@{CONFIG.db_host}/{CONFIG.db_name}",
    connect_args={"options": "-c timezone=UTC"},
)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)
