from functools import lru_cache

from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    secret_key: str = ""

    jwt_algorithm: str = "HS256"
    access_token_expires_minutes: int = 30

    db_host: str = ""
    db_name: str = ""
    db_username: str = ""
    db_password: str = ""

    frontend_urls: list[str] = ["http://192.168.1.159:3000", "http://127.0.0.1:3000"]
    send_verification_email: bool = True

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache()
def get_settings():
    return Settings()
