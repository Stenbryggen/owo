from pathlib import Path

from src.owo.components.growth import Growth
from src.owo.components.inventory import Inventory
from src.owo.components.position import Position
from src.owo.core.ecs import World
from src.owo.core.events import EventBus
from src.owo.core.planting import perform_plant
from src.owo.core.resource_types import load_resource_types

REPO_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_TYPES_DIR = REPO_ROOT / "content" / "resource_types"


def _make_world():
    world = World()
    world.resource_types = load_resource_types(str(RESOURCE_TYPES_DIR))
    return world


def test_planting_consumes_a_seed_and_spawns_a_sapling():
    world = _make_world()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Position(x=500, y=500))
    actor.add_component(Inventory(items={"seed": 1}))

    assert perform_plant(world, events, "Actor") is True
    assert "seed" not in actor.get_component(Inventory).items

    saplings = [e for e in world.entities.values() if e.get_component(Growth) is not None]
    assert len(saplings) == 1
    assert saplings[0].get_component(Growth).stage == "sapling"
    assert saplings[0].get_component(Position).x == 500


def test_planting_without_a_seed_fails():
    world = _make_world()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Position(x=0, y=0))
    actor.add_component(Inventory(items={}))

    assert perform_plant(world, events, "Actor") is False
    assert not any(e.get_component(Growth) is not None for e in world.entities.values())
