from pathlib import Path

from src.owo.components.growth import Growth
from src.owo.components.harvestable import Harvestable
from src.owo.components.position import Position
from src.owo.components.renderable import Renderable
from src.owo.core.ecs import World
from src.owo.core.events import EventBus
from src.owo.core.resource_types import load_resource_types
from src.owo.systems.tree_growth import TreeGrowthSystem

REPO_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_TYPES_DIR = REPO_ROOT / "content" / "resource_types"


def _make_world():
    world = World()
    world.resource_types = load_resource_types(str(RESOURCE_TYPES_DIR))
    return world


def _make_system(world):
    system = TreeGrowthSystem()
    system.setup(world, EventBus(), ai_provider=None)
    return system


def test_sapling_matures_after_enough_days():
    world = _make_world()
    sapling = world.create_entity("Sapling")
    sapling.add_component(Position(x=0, y=0))
    sapling.add_component(Renderable(kind="sapling"))
    sapling.add_component(Growth(stage="sapling", age_days=0, mature_at_days=3, reproduction_chance=0.0))
    sapling.add_component(Harvestable(resource_type="wood", amount=0.0, max_amount=6.0, on_depleted="remove"))

    system = _make_system(world)
    for day in range(1, 4):
        system._on_new_day({"day": day})

    growth = sapling.get_component(Growth)
    assert growth.stage == "mature"
    assert sapling.get_component(Renderable).kind == "tree"
    assert sapling.get_component(Harvestable).amount == 6.0


def test_sapling_not_yet_mature_stays_a_sapling():
    world = _make_world()
    sapling = world.create_entity("Sapling")
    sapling.add_component(Position(x=0, y=0))
    sapling.add_component(Renderable(kind="sapling"))
    sapling.add_component(Growth(stage="sapling", age_days=0, mature_at_days=3, reproduction_chance=0.0))

    system = _make_system(world)
    system._on_new_day({"day": 1})

    assert sapling.get_component(Growth).stage == "sapling"


def test_mature_tree_always_reproduces_when_chance_is_certain():
    world = _make_world()
    tree = world.create_entity("Tree")
    tree.add_component(Position(x=1000, y=1000))
    tree.add_component(Growth(stage="mature", reproduction_chance=1.0))
    tree.add_component(Harvestable(resource_type="wood", amount=6.0, max_amount=6.0, on_depleted="remove"))

    system = _make_system(world)
    system._on_new_day({"day": 1})

    saplings = [e for e in world.entities.values() if e is not tree and e.get_component(Growth)]
    assert len(saplings) == 1
    assert saplings[0].get_component(Growth).stage == "sapling"


def test_mature_tree_never_reproduces_when_chance_is_zero():
    world = _make_world()
    tree = world.create_entity("Tree")
    tree.add_component(Position(x=1000, y=1000))
    tree.add_component(Growth(stage="mature", reproduction_chance=0.0))
    tree.add_component(Harvestable(resource_type="wood", amount=6.0, max_amount=6.0, on_depleted="remove"))

    system = _make_system(world)
    for day in range(1, 11):
        system._on_new_day({"day": day})

    saplings = [e for e in world.entities.values() if e is not tree and e.get_component(Growth)]
    assert saplings == []


def test_reproduction_stops_once_local_density_cap_is_reached():
    from src.owo.systems.tree_growth import DENSITY_RADIUS, MAX_LOCAL_DENSITY

    world = _make_world()
    # Pack MAX_LOCAL_DENSITY mature trees tightly together, well within
    # DENSITY_RADIUS of each other.
    for i in range(MAX_LOCAL_DENSITY):
        tree = world.create_entity(f"Tree{i}")
        tree.add_component(Position(x=i * 10, y=0))
        tree.add_component(Growth(stage="mature", reproduction_chance=1.0))
        tree.add_component(Harvestable(resource_type="wood", amount=6.0, max_amount=6.0, on_depleted="remove"))

    assert MAX_LOCAL_DENSITY * 10 < DENSITY_RADIUS  # sanity check on the test's own geometry

    system = _make_system(world)
    entity_count_before = len(world.entities)
    system._on_new_day({"day": 1})

    # At the cap already - guaranteed reproduction chance still shouldn't add anyone.
    assert len(world.entities) == entity_count_before


def test_reproduction_resumes_once_below_the_density_cap():
    from src.owo.systems.tree_growth import MAX_LOCAL_DENSITY

    world = _make_world()
    for i in range(MAX_LOCAL_DENSITY - 1):
        tree = world.create_entity(f"Tree{i}")
        tree.add_component(Position(x=i * 10, y=0))
        tree.add_component(Growth(stage="mature", reproduction_chance=1.0))
        tree.add_component(Harvestable(resource_type="wood", amount=6.0, max_amount=6.0, on_depleted="remove"))

    system = _make_system(world)
    entity_count_before = len(world.entities)
    system._on_new_day({"day": 1})

    assert len(world.entities) > entity_count_before
