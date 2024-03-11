import os

from pydantic_settings import SettingsConfigDict, BaseSettings


class Config(BaseSettings):
    secret_key: str = ""

    jwt_algorithm: str = "HS256"
    access_token_expires_minutes: int = 30
    refresh_token_expires_days: int = 30

    postgres_host: str = ""
    postgres_db: str = ""
    postgres_user: str = ""
    postgres_password: str = ""

    redis_url: str = "redis://localhost:6379"

    frontend_url: str = ""

    verification_url: str = ""
    send_verification_email: bool = True

    edit_username_every_days: int = 30

    first_move_stall_timeout: int = 25
    disconnection_timeout: int = 60
    elo_k_factor: int = 15

    default_rating: int = 800
    acceptable_rating_difference: int = 300

    board_width: int = 10
    board_height: int = 10
    default_fen: str = (
        "rhnxqkbahr/ddpdppdpdd/c8c/10/10/10/10/C8C/DDPDPPDPDD/RHNXQKBAHR"
    )

    model_config = SettingsConfigDict(env_file=os.getenv("ENV") or ".env")


CONFIG = Config()


def get_config():
    return CONFIG
