from typing import TypeVar, Generic, Any, TYPE_CHECKING

import factory

T = TypeVar("T")


class TypedFactoryBase(Generic[T]):
    if TYPE_CHECKING:

        @classmethod
        def create(cls, *args: Any, **kwargs: Any) -> T:
            ...

        @classmethod
        def build(cls, *args: Any, **kwargs: Any) -> T:
            ...


class TypedFactory(Generic[T], TypedFactoryBase[T], factory.Factory):
    pass


class TypedSQLAlchemyFactory(
    Generic[T],
    TypedFactoryBase[T],
    factory.alchemy.SQLAlchemyModelFactory,
):
    pass
