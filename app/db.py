from contextlib import asynccontextmanager
import urllib.parse

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import MappedAsDataclass, DeclarativeBase
from fastapi import FastAPI


class Base(MappedAsDataclass, DeclarativeBase):
    pass


engine = create_async_engine(
    f"postgresql+asyncpg://postgres"
    f":{urllib.parse.quote_plus('qai6&@UHDt*BoH$NhgHk')}"
    "@127.0.0.1/chess2"
)
SessionLocal = async_sessionmaker(engine)


@asynccontextmanager
async def create_tables(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
