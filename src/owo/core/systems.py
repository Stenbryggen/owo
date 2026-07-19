from typing import List, Tuple, Type

from src.owo.core.ecs import Component, World
from src.owo.core.events import EventBus


class System:
    required_components: Tuple[Type[Component], ...] = ()

    def setup(self, events: EventBus) -> None:
        """Called once before the first update(); override to subscribe to events."""
        pass

    def update(self, world: World, config: dict, events: EventBus, dt: float) -> None:
        raise NotImplementedError


class SystemManager:
    def __init__(self, systems: List[System], events: EventBus):
        self._systems = systems
        self._events = events
        for system in self._systems:
            system.setup(self._events)

    def update(self, world: World, config: dict, dt: float) -> None:
        for system in self._systems:
            system.update(world, config, self._events, dt)
