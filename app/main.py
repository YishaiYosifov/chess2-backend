from contextlib import asynccontextmanager
from http import HTTPStatus

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, FastAPI

from app.schemas.config_schema import CONFIG
from app.websockets import ws_server_instance
from app.schemas import response_schema
from app.utils import common
from app.crud import user_crud
from app.db import engine, SessionLocal, Base
from app import deps

from .routers import game_requests, settings, profile, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    ws_server_instance.connect_pubsub()
    yield
    await ws_server_instance.disconnect_pubsub()

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


@app.websocket("/ws")
async def connect_websocket(
    websocket: WebSocket,
    user: deps.WSUnauthedUserDep,
    ws_server: deps.WSServerDep,
):
    await ws_server.connect_websocket(websocket, user.user_id)
