"""
DON'T USE THIS!
There is no reason to use a mocked db if we already setup an actual test db.
I don't want to delete this in case I change my mind.
"""

from unittest.mock import MagicMock, Mock
from typing import Sequence, Any

from app.db import Base


class DbMock(MagicMock):
    """Mock class for simulating an sqlalchemy database"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._pending_results: list[Sequence[Base]] = []
        self.in_session = []

    def add_result(self, *models: Base):
        """Add a list of models to the pending results"""
        self._pending_results.append(models)

    def execute(self, *args: Any, **kwargs: Any):
        "Simulate executing a query and return a MockResult containing the next pending result"

        result = self._pending_results.pop(0) if self._pending_results else []
        return MockResult(result=result)

    def add(self, model: Base):
        self.in_session.append(model)

    def add_all(self, models: list[Base]):
        for model in models:
            self.add(model)

    def delete(self, model: Base):
        self.in_session.remove(model)


class MockResult(MagicMock):
    """Mock class representing the result of an sqlalchemy query"""

    def __init__(self, result: Sequence[Base], *args: Any, **kw: Any) -> None:
        super().__init__(*args, **kw)
        self._result = result

    def scalar(self):
        return self._result[0] if self._result else None

    def scalars(self):
        return MockScalars(result=self._result)

    def all(self):
        return [(result,) for result in self._result]


class MockScalars(Mock):
    """Mock class representing scalar values of an sqlalchemy query"""

    def __init__(self, result: Sequence[Base], *args: Any, **kw: Any) -> None:
        super().__init__(*args, **kw)
        self._results = result
        self._index = 0

    def __iter__(self):
        return iter(self._results)

    def all(self):
        self._index = len(self._results)
        return self._results
