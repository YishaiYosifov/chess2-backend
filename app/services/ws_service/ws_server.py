from __future__ import annotations

import asyncio
import json

from fastapi import status, WebSocketException, WebSocket
import redis.asyncio as aioredis

from app.services.ws_service.client_manager import (
    ABCWebsocketClientManager,
    WebsocketClientManager,
)
from app.services.ws_service.ws_router import WSRouter
from app import enums


class WSServer(WSRouter):
    def __init__(
        self,
        redis_client: aioredis.Redis,
        pubsub_channel: str = "websocket_emits",
        client_manager: ABCWebsocketClientManager | None = None,
    ):
        self.clients = client_manager or WebsocketClientManager()

        self._pubsub_channel = pubsub_channel
        self._redis = redis_client

        super().__init__()

    async def connect_websocket(
        self,
        websocket: WebSocket,
        user_id: int,
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
                self._handle_message(message)
        finally:
            self.clients.remove_client(user_id)

    async def emit(
        self,
        event: enums.WSEvent,
        data: dict,
        to: str | int,
    ) -> None:
        """
        Emit a message to a user or a room.

        :param event: the websocket event to emit with
        :param data: the data to emit
        :param to: an id of a user or a name of a room
        """

        data_str = json.dumps(data)
        await self._redis.publish(
            self._pubsub_channel,
            f"{to}:{event.value}:{data_str}",
        )

    def include_router(self, router: WSRouter):
        self._event_handlers.update(router)

    async def connect_pubsub(self) -> None:
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(self._pubsub_channel)

        self._pubsub_task = asyncio.create_task(self._handle_pubsub())

    async def disconnect_pubsub(self) -> None:
        self._pubsub_task.cancel()
        await self._pubsub_task

        await self._pubsub.aclose()

    def _handle_message(self, message: str) -> None:
        """
        Try to forward a message recived from the
        client into the correct even handler

        :param message: the message received from the client
        """

        invalid_protocol_err = WebSocketException(status.WS_1002_PROTOCOL_ERROR)

        # make sure the event is valid
        try:
            event, data = message.split(":", 1)
            event = enums.WSEvent(event)
        except ValueError:
            raise invalid_protocol_err

        # make sure there is an even handler for this event
        event_handler = self._event_handlers.get(event)
        if not event_handler:
            return

        # try to load the data into a dictionary
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            raise invalid_protocol_err
        if not isinstance(data, dict):
            raise invalid_protocol_err

        event_handler(self, data)

    async def _handle_pubsub(self) -> None:
        """
        Handle emit messages from different servers.
        Forwards messages to the correct connected clients
        """

        while True:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1
                )
            except asyncio.CancelledError:
                return

            if not message or message["type"] != "message":
                await asyncio.sleep(0)
                continue

            data: bytes = message["data"]
            clients_id, message = data.decode("utf-8").split(":", 1)

            for client in self.clients.get_clients(clients_id):
                await client.send_text(message)
