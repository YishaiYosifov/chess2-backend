from fastapi import FastAPI

from .routers import auth
from .db import create_tables

app = FastAPI(lifespan=create_tables)
app.include_router(auth.router)
