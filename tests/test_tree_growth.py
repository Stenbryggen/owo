from src.owo.components.growth import Growth
from src.owo.components.harvestable import Harvestable
from src.owo.components.position import Position
from src.owo.components.renderable import Renderable
from src.owo.core.ecs import World
from src.owo.core.events import EventBus
from src.owo.systems.tree_growth import TreeGrowthSystem


def _make_system(world):
    system = TreeGrowthSystem()
    system.setup(world, EventBus(), ai_provider=None)
    return system


def test_sapling_matures_after_enough_days():
    world = World()
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
    world = World()
    sapling = world.create_entity("Sapling")
    sapling.add_component(Position(x=0, y=0))
    sapling.add_component(Renderable(kind="sapling"))
    sapling.add_component(Growth(stage="sapling", age_days=0, mature_at_days=3, reproduction_chance=0.0))

    system = _make_system(world)
    system._on_new_day({"day": 1})

    assert sapling.get_component(Growth).stage == "sapling"


def test_mature_tree_always_reproduces_when_chance_is_certain():
    world = World()
    tree = world.create_entity("Tree")
    tree.add_component(Position(x=1000, y=1000))
    tree.add_component(Growth(stage="mature", reproduction_chance=1.0))

    system = _make_system(world)
    system._on_new_day({"day": 1})

    saplings = [e for e in world.entities.values() if e is not tree and e.get_component(Growth)]
    assert len(saplings) == 1
    assert saplings[0].get_component(Growth).stage == "sapling"


def test_mature_tree_never_reproduces_when_chance_is_zero():
    world = World()
    tree = world.create_entity("Tree")
    tree.add_component(Position(x=1000, y=1000))
    tree.add_component(Growth(stage="mature", reproduction_chance=0.0))

    system = _make_system(world)
    for day in range(1, 11):
        system._on_new_day({"day": day})

    saplings = [e for e in world.entities.values() if e is not tree and e.get_component(Growth)]
    assert saplings == []
