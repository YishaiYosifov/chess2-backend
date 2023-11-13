from http import HTTPStatus

from fastapi import FastAPI

from app.schemas.response_schema import ErrorResponse
from app.db import engine, Base

from .routers import settings, profile, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chess2",
    responses={
        HTTPStatus.UNAUTHORIZED: {
            "description": "Could not verify credentials",
            "model": ErrorResponse[str],
        },
    },
)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(settings.router)
