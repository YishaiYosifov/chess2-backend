from typing import Generator
from abc import abstractmethod, ABC

from fastapi import WebSocket


class ABCWebsocketClientManager(ABC):
    @abstractmethod
    def get_clients(self, id: str | int) -> Generator[WebSocket, None, None]:
        pass

    @abstractmethod
    def add_client(self, user_id: int, client: WebSocket) -> None:
        pass

    @abstractmethod
    def remove_client(self, user_id: int) -> None:
        pass

    @abstractmethod
    def enter_room(self, room_name: str, user_id: int) -> None:
        pass

    @abstractmethod
    def leave_room(self, room_name: str, user_id: int) -> None:
        pass

    @abstractmethod
    def close_room(self, room_name: str) -> None:
        pass


class WebsocketClientManager(ABCWebsocketClientManager):
    def __init__(self) -> None:
        self._rooms: dict[str, set[int]] = {}
        self._clients: dict[int, WebSocket] = {}

    def get_clients(self, ids: str | int) -> Generator[WebSocket, None, None]:
        """
        Get the clients connected to a room, or the client of a user

        :param ids: a room name or a user id

        :return: a generator the yields with the client instances
        """

        if isinstance(ids, int) or ids.isnumeric():
            id = int(ids)
            if id in self._clients:
                yield self._clients[id]
            return

        client_ids = self._rooms.get(ids, set())
        for client_id in client_ids:
            yield self._clients[client_id]

    def add_client(self, user_id: int, client: WebSocket) -> None:
        self._clients[user_id] = client

    def remove_client(self, user_id: int) -> None:
        self._clients.pop(user_id, None)

    def enter_room(self, room_name: str, user_id: int) -> None:
        if room_name not in self._rooms:
            self._rooms[room_name] = {user_id}
        else:
            self._rooms[room_name].add(user_id)

    def leave_room(self, room_name: str, user_id: int) -> None:
        self._rooms[room_name].remove(user_id)
        if not self._rooms[room_name]:
            self._rooms.pop(room_name)

    def close_room(self, room_name: str) -> None:
        self._rooms.pop(room_name, None)
