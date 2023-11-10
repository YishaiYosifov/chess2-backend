from typing import Any
import shutil
import os

from pydantic.main import _model_construction
from pydantic import BaseModel


class PartialModel(_model_construction.ModelMetaclass):
    """Make every field in a pydantic model optional"""

    def __new__(
        cls,
        name: str,
        bases: tuple[Any, ...],
        namespaces: dict[str, Any],
        **kwargs: Any,
    ):
        for base in bases:
            if not issubclass(base, BaseModel):
                continue

            # If the base is a pydantic model, loop over its fields and set the default value to None
            # thus making it optional
            for field in base.model_fields.values():
                field.default = None

        return super().__new__(cls, name, bases, namespaces, **kwargs)


def create_or_replace_folder(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)

    os.makedirs(path)


def get_or_create_uploads_folder(user_id: int):
    uploads_path = os.path.join("uploads", str(user_id))
    if not os.path.exists(uploads_path):
        create_or_replace_folder(uploads_path)

    return os.path.join("uploads", str(user_id))
