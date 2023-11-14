from collections import defaultdict
from typing import Callable, TypeVar
import shutil
import os


def create_or_replace_folder(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)

    os.makedirs(path)


def get_or_create_uploads_folder(user_id: int):
    uploads_path = os.path.join("uploads", str(user_id))
    if not os.path.exists(uploads_path):
        create_or_replace_folder(uploads_path)

    return os.path.join("uploads", str(user_id))


_K = TypeVar("_K")
_V = TypeVar("_V")


def defaultdict_fromkeys(
    value_type: Callable[[], _V],
    default_keys: list[_K],
) -> defaultdict[_K, _V]:
    return defaultdict(value_type, {key: value_type() for key in default_keys})
