import os


def get_uploads_path(user_id: int):
    return os.path.join("uploads", str(user_id))
