from __future__ import annotations

from typing import Concatenate, Callable, Any, TYPE_CHECKING

from app import enums

if TYPE_CHECKING:
    from app.services.ws_service.ws_server import WSServer


EventHandlerFunc = Callable[Concatenate["WSServer", dict, ...], Any]


class WSRouter:
    def __init__(self) -> None:
        self._event_handlers: dict[enums.WSEventIn, EventHandlerFunc] = {}

    def __iter__(self):
        return iter(self._event_handlers.items())

    def on_event(self, event: enums.WSEventIn):
        """Register a function to a websocket event"""

        def decorator(func: EventHandlerFunc):
            self._event_handlers[event] = func
            return func

        return decorator
