import urllib.parse

from sqlalchemy.orm import sessionmaker, MappedAsDataclass, DeclarativeBase
from sqlalchemy import create_engine

from app.schemas.config_schema import get_config


class Base(MappedAsDataclass, DeclarativeBase):
    pass


config = get_config()
engine = create_engine(
    "postgresql+psycopg2://"
    f"{config.db_username}:{urllib.parse.quote_plus(config.db_password)}"
    f"@{config.db_host}/{config.db_name}",
    connect_args={"options": "-c timezone=UTC"},
)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)
