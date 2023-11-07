from typing import Annotated

from sqlalchemy.orm import Session
from fastapi import Depends

from .schemas.config import get_settings, Settings
from .db import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
