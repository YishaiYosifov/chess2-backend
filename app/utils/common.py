from typing import Concatenate, Callable, Any
import shutil
import uuid
import os

from sqlalchemy.orm import sessionmaker, Session


def create_or_replace_folder(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)

    os.makedirs(path)


def get_or_create_uploads_folder(user_id: int) -> str:
    uploads_path = os.path.join("uploads", str(user_id))
    if not os.path.exists(uploads_path):
        create_or_replace_folder(uploads_path)

    return os.path.join("uploads", str(user_id))


def truncated_uuid(truncate: int = 15) -> str:
    return uuid.uuid4().hex[:truncate]


def run_with_db(
    session_local: sessionmaker[Session],
    func: Callable[Concatenate[Session, ...], None],
    *args: Any,
    **kwargs: Any,
) -> None:
    db = session_local()
    try:
        func(db, *args, **kwargs)
    finally:
        db.close()
