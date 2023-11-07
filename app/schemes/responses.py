from typing import TypeVar

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    details: dict | list | str


class ConflictResponse(ErrorResponse):
    details: dict[str, str]
