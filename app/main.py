from fastapi import FastAPI

from app.db import engine, Base

from .routers import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chess2")
app.include_router(auth.router)
