from typing import Awaitable, Callable
import asyncio
import json

from fastapi import WebSocket
import redis.asyncio as redis

from app.websockets.client_manager import (
    ABCWebsocketClientManager,
    WebsocketClientManager,
)


class WSServer:
    def __init__(
        self,
        redis_url: str,
        pubsub_channel: str = "websocket_emits",
        client_service: ABCWebsocketClientManager | None = None,
    ):
        self._pubsub_channel = pubsub_channel
        self.clients = client_service or WebsocketClientManager()

        self.connect(redis_url)

    async def connect_websocket(
        self,
        websocket: WebSocket,
        user_id: int,
        on_receive: Callable[[str], Awaitable[None]] | None = None,
    ) -> None:
        """
        Subsribe a websocket client to a channel

        :param websocket: the websocket client
        :param channel: the channel to connect the client to
        :param on_receive: a function to call when a message is received
        """

        await websocket.accept()
        self.clients.add_client(user_id, websocket)

        try:
            async for message in websocket.iter_text():
                if on_receive:
                    on_receive(message)
        finally:
            self.clients.remove_client(user_id)

    async def emit(self, message: dict, clients_id: str | int):
        """
        Emit a message to a user or a room.

        :param clients_id: an id of a user or a name of a room
        """

        message_str = json.dumps(message)
        await self._redis.publish(
            self._pubsub_channel, f"{clients_id}:{message_str}"
        )

    async def _handle_pubsub(self):
        """
        Handle emit messages from different servers.
        Forwards messages to the correct connected clients
        """

        await self._pubsub.subscribe(self._pubsub_channel)
        async for message in self._pubsub.listen():
            if message["type"] != "message":
                continue

            data: bytes = message["data"]
            clients_id, message = data.decode("utf-8").split(":")
            for client in self.clients.get_clients(clients_id):
                await client.send_text(message)

    def connect(self, redis_url: str):
        self._redis = redis.Redis.from_url(redis_url)
        self._pubsub = self._redis.pubsub()

    def initilize(self):
        self._pubsub_task = asyncio.create_task(self._handle_pubsub())

    async def disconnect(self):
        if hasattr(self, "_pubsub_task") and self._pubsub_task:
            self._pubsub_task.cancel()

        await self._pubsub.close()
        await self._redis.close()
