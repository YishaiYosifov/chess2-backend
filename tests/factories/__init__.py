from typing import TypeVar, Generic

from factory.base import FactoryMetaClass

from app.dependencies import get_db
from app.main import app


class BaseMeta:
    sqlalchemy_session_factory = lambda: app.dependency_overrides[get_db]()
    sqlalchemy_session = None
    sqlalchemy_session_persistence = "commit"


T = TypeVar("T")


class BaseMetaFactory(FactoryMetaClass, Generic[T]):
    def __call__(cls, *args, **kwargs) -> T:
        return super().__call__(*args, **kwargs)  # type: ignore
