import os


def get_uploads_path(user_id: int):
    return os.path.join("uploads", str(user_id))


def snake_to_camel(to_convert: str) -> str:
    """Convert from snake_case to camelCase"""

    return "".join(
        [
            word.title() if index else word
            for index, word in enumerate(to_convert.split("_"))
        ]
    )
