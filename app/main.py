from http import HTTPStatus

from fastapi import FastAPI

from app.schemas.responses import ResponseError
from app.db import engine, Base

from .routers import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chess2",
    responses={
        HTTPStatus.UNAUTHORIZED: {
            "description": "Could not verify credentials",
            "model": ResponseError[str],
        },
    },
)
app.include_router(auth.router)
