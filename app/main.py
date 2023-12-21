from http import HTTPStatus

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.schemas.config_schema import get_config
from app.schemas import response_schema
from app.db import engine, Base

from .routers import game_requests, settings, profile, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chess2",
    responses={
        HTTPStatus.UNAUTHORIZED: {
            "description": "Could not verify credentials",
            "model": response_schema.ErrorResponse[str],
        },
    },
)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(settings.router)
app.include_router(game_requests.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_config().frontend_url,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
