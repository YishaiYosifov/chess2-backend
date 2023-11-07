from typing import TypeVar, Generic

from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseSQLAlchemyModelFactory(SQLAlchemyModelFactory, Generic[T]):
    class Meta:
        sqlalchemy_session_persistence = "commit"

    @classmethod
    def create(cls, session: Session, **kwargs) -> T:
        cls._meta.sqlalchemy_session = session  # type: ignore
        return super().create(**kwargs)
