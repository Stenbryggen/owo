import uuid

from src.owo.components.growth import Growth
from src.owo.components.harvestable import Harvestable
from src.owo.components.position import Position
from src.owo.components.renderable import Renderable

TREE_MAX_WOOD = 6.0
MINE_MAX_STONE = 20.0
MINE_REGEN_PER_HOUR = 0.5


def spawn_tree(world, x: float, y: float, mature: bool = True):
    entity = world.create_entity(f"Tree_{uuid.uuid4().hex[:8]}")
    entity.add_component(Position(x=x, y=y))
    entity.add_component(Renderable(kind="tree" if mature else "sapling"))
    entity.add_component(Growth(
        stage="mature" if mature else "sapling",
        age_days=0, mature_at_days=3, reproduction_chance=0.15,
    ))
    entity.add_component(Harvestable(
        resource_type="wood",
        amount=TREE_MAX_WOOD if mature else 0.0,
        max_amount=TREE_MAX_WOOD,
        required_tool="axe",
        on_depleted="remove",
    ))
    return entity


def spawn_mine(world, x: float, y: float):
    entity = world.create_entity(f"Mine_{uuid.uuid4().hex[:8]}")
    entity.add_component(Position(x=x, y=y))
    entity.add_component(Renderable(kind="mine"))
    entity.add_component(Harvestable(
        resource_type="stone",
        amount=MINE_MAX_STONE,
        max_amount=MINE_MAX_STONE,
        regen_per_hour=MINE_REGEN_PER_HOUR,
        required_tool="pickaxe",
        on_depleted="regen",
        depleted_kind="empty_mine",
        full_kind="mine",
    ))
    return entity
