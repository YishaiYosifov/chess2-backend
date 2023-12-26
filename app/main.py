from contextlib import asynccontextmanager
from http import HTTPStatus

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi import FastAPI

from app.schemas.config_schema import get_config, CONFIG
from app.schemas import response_schema
from app.utils import common
from app.crud import guest_crud
from app.db import engine, SessionLocal, Base

from .routers import game_requests, settings, profile, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Delete inactive guest accounts every day at 12am
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: common.run_with_db(
            SessionLocal,
            guest_crud.delete_inactive_guests,
            CONFIG.access_token_expires_minutes,
        ),
        "cron",
        hour=0,
    )

    scheduler.start()
    yield
    scheduler.shutdown()


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chess2",
    responses={
        HTTPStatus.UNAUTHORIZED: {
            "description": "Could not verify credentials",
            "model": response_schema.ErrorResponse[str],
        },
    },
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
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
