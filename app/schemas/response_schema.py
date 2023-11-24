from typing import TypeVar, Generic

from pydantic import BaseModel

E = TypeVar("E", dict, str, list)


class ErrorResponse(BaseModel, Generic[E]):
    details: E
