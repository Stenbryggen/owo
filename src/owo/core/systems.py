from typing import List, Tuple, Type

from src.owo.core.ecs import Component, World
from src.owo.core.events import EventBus


class System:
    required_components: Tuple[Type[Component], ...] = ()

    def setup(self, world: World, events: EventBus, ai_provider) -> None:
        """Called once before the first update(); override to subscribe to
        events or stash world/ai_provider for event handlers that fire
        outside the regular per-tick update() (e.g. NpcAutonomySystem)."""
        pass

    def update(self, world: World, config: dict, events: EventBus, dt: float) -> None:
        raise NotImplementedError


class SystemManager:
    def __init__(self, systems: List[System], world: World, events: EventBus, ai_provider):
        self._systems = systems
        self._events = events
        for system in self._systems:
            system.setup(world, events, ai_provider)

    def update(self, world: World, config: dict, dt: float) -> None:
        for system in self._systems:
            system.update(world, config, self._events, dt)
