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
