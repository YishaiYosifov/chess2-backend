from http import HTTPStatus

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.schemas.response_schema import ErrorResponse
from app.schemas.config_schema import get_settings
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().frontend_urls,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
