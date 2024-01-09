from contextlib import asynccontextmanager
from http import HTTPStatus

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.schemas.config_schema import CONFIG
from app.schemas import response_schema
from app.utils import common
from app.crud import user_crud
from app.ws import broadcast
from app.db import engine, SessionLocal, Base

from .routers import game_requests, settings, profile, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broadcast.connect()

    # Delete inactive guest accounts every day at 12am
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: common.run_with_db(
            SessionLocal,
            user_crud.delete_inactive_guests,
            CONFIG.access_token_expires_minutes,
        ),
        "cron",
        hour=0,
    )

    scheduler.start()

    yield

    await broadcast.disconnect()
    scheduler.shutdown()


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chess2",
    responses={
        HTTPStatus.UNAUTHORIZED: {
            "description": "Could not verify credentials",
            "model": response_schema.ErrorResponse[str],
        },
    },
    generate_unique_id_function=lambda route: f"{route.tags[0]}-{route.name}",
    lifespan=lifespan,
)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(settings.router)
app.include_router(game_requests.router)

# openapi-generator doesn't support 3.1.0 "yet"
# https://github.com/OpenAPITools/openapi-generator/issues/9083
app.openapi_version = "3.0.3"

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.frontend_url,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
