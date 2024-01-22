from typing import Awaitable, Callable
import asyncio
import json

from fastapi import WebSocket
import redis.asyncio as aioredis

from app.websockets.client_manager import (
    ABCWebsocketClientManager,
    WebsocketClientManager,
)


class WSServer:
    def __init__(
        self,
        redis_client: aioredis.Redis,
        pubsub_channel: str = "websocket_emits",
        client_manager: ABCWebsocketClientManager | None = None,
    ):
        self.clients = client_manager or WebsocketClientManager()
        self._pubsub_channel = pubsub_channel
        self._redis = redis_client

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

    async def emit(self, message: dict, to: str | int):
        """
        Emit a message to a user or a room.

        :param to: an id of a user or a name of a room
        """

        message_str = json.dumps(message)
        await self._redis.publish(
            self._pubsub_channel,
            f"{to}:{message_str}",
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

    def connect_pubsub(self):
        self._pubsub = self._redis.pubsub()
        self._pubsub_task = asyncio.create_task(self._handle_pubsub())

    async def disconnect_pubsub(self):
        self._pubsub_task.cancel()
        await self._pubsub.aclose()
