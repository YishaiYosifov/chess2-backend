from functools import lru_cache
import os

from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    secret_key: str = ""

    jwt_algorithm: str = "HS256"
    access_token_expires_minutes: int = 30
    refresh_token_expires_days: int = 30

    db_host: str = ""
    db_name: str = ""
    db_username: str = ""
    db_password: str = ""

    frontend_url: str = ""

    verification_url: str = ""
    send_verification_email: bool = True

    edit_username_every_days: int = 30

    model_config = SettingsConfigDict(env_file=os.getenv("ENV"))


@lru_cache()
def get_settings():
    return Settings()
