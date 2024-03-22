from app.db import redis_client

from .ws_server import WSServer

ws_server_inst = WSServer(redis_client)
