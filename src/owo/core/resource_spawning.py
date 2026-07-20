import uuid

from src.owo.components.growth import Growth
from src.owo.components.harvestable import Harvestable
from src.owo.components.motion import Motion
from src.owo.components.position import Position
from src.owo.components.renderable import Renderable
from src.owo.core.resource_types import ResourceType

# Structure kinds that also grant an aura effect (see core/movement.py) once
# placed, keyed by kind -> speed_bonus. A crafted cart works the same as
# the hand-placed starting one.
STRUCTURE_SPEED_BONUS = {"cart": 0.6}


def spawn_resource(world, x: float, y: float, resource_type: ResourceType, mature: bool = True, name: str = None):
    """Builds one harvestable entity from a ResourceType (see
    core/resource_types.py) - the one generic constructor every world-
    generated or content-placed resource (tree, mine, bush, ...) goes
    through, so a brand new resource type never needs a new Python
    function, only a new content/resource_types/*.json file. `name`
    overrides the auto-generated one - used for hand-placed starting
    resources that need a stable, referenceable name (e.g. "Tree1")."""
    entity = world.create_entity(
        name or f"{resource_type.name.title().replace('_', '')}_{uuid.uuid4().hex[:8]}"
    )
    entity.add_component(Position(x=x, y=y))

    growth = resource_type.growth
    kind = resource_type.renderable_kind if (mature or not growth.enabled) else growth.sapling_kind
    entity.add_component(Renderable(kind=kind))

    if growth.enabled:
        entity.add_component(Growth(
            stage="mature" if mature else "sapling",
            age_days=0,
            mature_at_days=growth.mature_at_days,
            reproduction_chance=growth.reproduction_chance,
        ))

    entity.add_component(Harvestable(
        resource_type=resource_type.resource_type,
        amount=resource_type.max_amount if mature else 0.0,
        max_amount=resource_type.max_amount,
        regen_per_hour=resource_type.regen_per_hour,
        required_tool=resource_type.required_tool,
        on_depleted=resource_type.on_depleted,
        depleted_kind=resource_type.depleted_kind,
        full_kind=resource_type.renderable_kind,
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
