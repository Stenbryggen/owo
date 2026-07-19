import uuid

from src.owo.components.growth import Growth
from src.owo.components.harvestable import Harvestable
from src.owo.components.motion import Motion
from src.owo.components.position import Position
from src.owo.components.renderable import Renderable

# Structure kinds that also grant an aura effect (see core/movement.py) once
# placed, keyed by kind -> speed_bonus. A crafted cart works the same as
# the hand-placed starting one.
STRUCTURE_SPEED_BONUS = {"cart": 0.6}

TREE_MAX_WOOD = 6.0
MINE_MAX_STONE = 20.0
MINE_REGEN_PER_HOUR = 0.5
ORE_MINE_MAX_IRON = 12.0
ORE_MINE_REGEN_PER_HOUR = 0.3
BUSH_MAX_FIBER = 3.0
BUSH_REGEN_PER_HOUR = 1.0


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


def spawn_ore_mine(world, x: float, y: float):
    entity = world.create_entity(f"OreMine_{uuid.uuid4().hex[:8]}")
    entity.add_component(Position(x=x, y=y))
    entity.add_component(Renderable(kind="ore_mine"))
    entity.add_component(Harvestable(
        resource_type="iron",
        amount=ORE_MINE_MAX_IRON,
        max_amount=ORE_MINE_MAX_IRON,
        regen_per_hour=ORE_MINE_REGEN_PER_HOUR,
        required_tool="pickaxe",
        on_depleted="regen",
        depleted_kind="empty_mine",
        full_kind="ore_mine",
    ))
    return entity


def spawn_bush(world, x: float, y: float):
    entity = world.create_entity(f"Bush_{uuid.uuid4().hex[:8]}")
    entity.add_component(Position(x=x, y=y))
    entity.add_component(Renderable(kind="bush"))
    entity.add_component(Harvestable(
        resource_type="fiber",
        amount=BUSH_MAX_FIBER,
        max_amount=BUSH_MAX_FIBER,
        regen_per_hour=BUSH_REGEN_PER_HOUR,
        on_depleted="regen",
        depleted_kind="empty_bush",
        full_kind="bush",
    ))
    return entity


def spawn_structure(world, x: float, y: float, kind: str, name_prefix: str = "Structure"):
    """A crafted, placed structure (workbench, tent, cart, boat, house...).
    Just a positioned, renderable prop - no harvestable/growth behavior,
    except for kinds in STRUCTURE_SPEED_BONUS (e.g. a cart), which also
    get the same Motion aura as the hand-placed starting one."""
    entity = world.create_entity(f"{name_prefix}_{uuid.uuid4().hex[:8]}")
    entity.add_component(Position(x=x, y=y))
    entity.add_component(Renderable(kind=kind))
    if kind in STRUCTURE_SPEED_BONUS:
        entity.add_component(Motion(speed_bonus=STRUCTURE_SPEED_BONUS[kind]))
    return entity
