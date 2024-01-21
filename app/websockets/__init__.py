from app.websockets.ws_server import WSServer
from app.db import redis_client

ws_server_instance = WSServer(redis_client)
