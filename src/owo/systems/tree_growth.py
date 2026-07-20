import math
import random

from src.owo.components.growth import Growth
from src.owo.components.harvestable import Harvestable
from src.owo.components.position import Position
from src.owo.components.renderable import Renderable
from src.owo.core.registry import register_system
from src.owo.core.resource_spawning import spawn_resource
from src.owo.core.systems import System

REPRODUCTION_RADIUS = 150.0
# Without a cap, reproduction is unconstrained exponential growth: every
# mature tree rolls its chance every day regardless of how crowded its
# neighborhood already is, and new saplings mature and start reproducing
# too. Measured: 18 -> 136,591 entities over 90 in-game days with no cap,
# accelerating (world_to_dict()/rendering/autosave all scale with entity
# count, so this was the actual cause of the game slowing down over time).
# A local density limit - a real forest's carrying capacity - keeps
# reproduction going only where there's still room.
DENSITY_RADIUS = 300.0
MAX_LOCAL_DENSITY = 6


@register_system("tree_growth")
class TreeGrowthSystem(System):
    """Event-driven on "new_day" (published by TimeSeasonSystem), same
    pattern as NpcAutonomySystem: saplings age up, and mature specimens
    occasionally seed a new one nearby, up to a local density cap - "trees
    that grow and make new trees" from the doc's ask. Not actually
    tree-specific: it drives every ResourceType with growth.enabled (see
    core/resource_types.py), so a new growable resource just needs that
    flag in its JSON, no new system."""

    def setup(self, world, events, ai_provider):
        self._world = world
        events.subscribe("new_day", self._on_new_day)

    def update(self, world, config, events, dt):
        pass

    def _resource_type_for(self, harvestable: Harvestable):
        return next(
            (rt for rt in self._world.resource_types.values()
             if rt.growth.enabled and rt.resource_type == harvestable.resource_type),
            None,
        )

    def _local_density(self, pos: Position, item_name: str) -> int:
        count = 0
        for entity in self._world.entities.values():
            if entity.get_component(Growth) is None:
                continue
            harvestable = entity.get_component(Harvestable)
            if harvestable is None or harvestable.resource_type != item_name:
                continue
            other_pos = entity.get_component(Position)
            if other_pos is None:
                continue
            if math.hypot(other_pos.x - pos.x, other_pos.y - pos.y) <= DENSITY_RADIUS:
                count += 1
        return count

    def _on_new_day(self, payload):
        new_spawns = []  # (x, y, resource_type)

        for entity in list(self._world.entities.values()):
            growth = entity.get_component(Growth)
            if growth is None:
                continue

            growth.age_days += 1
            if growth.stage != "mature" and growth.age_days >= growth.mature_at_days:
                self._mature(entity, growth)

            if growth.stage == "mature" and random.random() < growth.reproduction_chance:
                pos = entity.get_component(Position)
                harvestable = entity.get_component(Harvestable)
                resource_type = self._resource_type_for(harvestable) if harvestable else None
                if pos is None or resource_type is None:
                    continue
                if self._local_density(pos, resource_type.resource_type) < MAX_LOCAL_DENSITY:
                    new_spawns.append((pos.x, pos.y, resource_type))

        for x, y, resource_type in new_spawns:
            offset_x = x + random.uniform(-REPRODUCTION_RADIUS, REPRODUCTION_RADIUS)
            offset_y = y + random.uniform(-REPRODUCTION_RADIUS, REPRODUCTION_RADIUS)
            spawn_resource(self._world, offset_x, offset_y, resource_type, mature=False)

    def _mature(self, entity, growth: Growth) -> None:
        growth.stage = "mature"

        harvestable = entity.get_component(Harvestable)
        resource_type = self._resource_type_for(harvestable) if harvestable else None

        renderable = entity.get_component(Renderable)
        if renderable is not None and resource_type is not None:
            renderable.kind = resource_type.renderable_kind

        if harvestable is not None:
            harvestable.amount = harvestable.max_amount
