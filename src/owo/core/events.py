from collections import defaultdict
from typing import Any, Callable, Dict, List

EventHandler = Callable[[dict], None]


class EventBus:
    """Simple synchronous, in-process publish/subscribe bus."""

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._handlers[event_name].append(handler)

    def publish(self, event_name: str, payload: dict = None) -> None:
        for handler in list(self._handlers.get(event_name, [])):
            handler(payload or {})
