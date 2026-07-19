import random

from src.owo.components.growth import Growth
from src.owo.components.harvestable import Harvestable
from src.owo.components.position import Position
from src.owo.components.renderable import Renderable
from src.owo.core.registry import register_system
from src.owo.core.resource_spawning import spawn_tree
from src.owo.core.systems import System

REPRODUCTION_RADIUS = 150.0


@register_system("tree_growth")
class TreeGrowthSystem(System):
    """Event-driven on "new_day" (published by TimeSeasonSystem), same
    pattern as NpcAutonomySystem: saplings age up into full trees, and
    mature trees occasionally seed a new sapling nearby - "trees that grow
    and make new trees" from the doc's ask."""

    def setup(self, world, events, ai_provider):
        self._world = world
        events.subscribe("new_day", self._on_new_day)

    def update(self, world, config, events, dt):
        pass

    def _on_new_day(self, payload):
        new_sapling_spots = []

        for entity in list(self._world.entities.values()):
            growth = entity.get_component(Growth)
            if growth is None:
                continue

            growth.age_days += 1
            if growth.stage != "mature" and growth.age_days >= growth.mature_at_days:
                self._mature(entity, growth)

            if growth.stage == "mature" and random.random() < growth.reproduction_chance:
                pos = entity.get_component(Position)
                if pos is not None:
                    new_sapling_spots.append((pos.x, pos.y))

        for x, y in new_sapling_spots:
            offset_x = x + random.uniform(-REPRODUCTION_RADIUS, REPRODUCTION_RADIUS)
            offset_y = y + random.uniform(-REPRODUCTION_RADIUS, REPRODUCTION_RADIUS)
            spawn_tree(self._world, offset_x, offset_y, mature=False)

    def _mature(self, entity, growth: Growth) -> None:
        growth.stage = "mature"

        renderable = entity.get_component(Renderable)
        if renderable is not None:
            renderable.kind = "tree"

        harvestable = entity.get_component(Harvestable)
        if harvestable is not None:
            harvestable.amount = harvestable.max_amount
