import shutil
import uuid
import os


def create_or_replace_folder(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)

    os.makedirs(path)


def get_or_create_uploads_folder(user_id: int) -> str:
    uploads_path = os.path.join("uploads", str(user_id))
    if not os.path.exists(uploads_path):
        create_or_replace_folder(uploads_path)

    return os.path.join("uploads", str(user_id))


def truncated_uuid(truncate: int = 15):
    return uuid.uuid4().hex[:truncate]
