import urllib.parse

from sqlalchemy.orm import sessionmaker, MappedAsDataclass, DeclarativeBase
from sqlalchemy import create_engine

from app.schemes.config import get_settings


class Base(MappedAsDataclass, DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(
    "postgresql+psycopg2://"
    f"{settings.db_username}:{urllib.parse.quote_plus(settings.db_password)}"
    f"@{settings.db_host}/{settings.db_name}"
)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)
