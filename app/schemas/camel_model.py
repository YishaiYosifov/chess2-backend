from pydantic_settings import SettingsConfigDict
from pydantic import BaseModel

from app.utils.common import snake_to_camel


class CamelModel(BaseModel):
    model_config = SettingsConfigDict(
        populate_by_name=True,
        alias_generator=snake_to_camel,
    )
