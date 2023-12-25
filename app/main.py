from contextlib import asynccontextmanager
from http import HTTPStatus

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi import FastAPI

from app.schemas.config_schema import get_config, CONFIG
from app.schemas import response_schema
from app.crud import guest_crud
from app.db import engine, SessionLocal, Base

from .routers import game_requests, settings, profile, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    def run_delete_inactive():
        db = SessionLocal()
        try:
            guest_crud.delete_inactive_guests(
                db,
                CONFIG.access_token_expires_minutes,
            )
            db.commit()
        finally:
            db.close()

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_delete_inactive,
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
