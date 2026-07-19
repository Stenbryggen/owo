from src.owo.components.growth import Growth
from src.owo.components.harvestable import Harvestable
from src.owo.components.inventory import Inventory
from src.owo.components.position import Position
from src.owo.components.renderable import Renderable
from src.owo.components.skills import Skills
from src.owo.core.ecs import World
from src.owo.core.events import EventBus
from src.owo.core.harvest import perform_harvest
from src.owo.systems.resource_regen import ResourceRegenSystem

CONFIG = {}


def _make_actor(world, name="Actor", tools=None):
    entity = world.create_entity(name)
    entity.add_component(Inventory(items=dict(tools or {})))
    entity.add_component(Skills(levels={"wood": 1, "stone": 1}))
    return entity


def test_harvesting_a_mine_without_a_tool_is_slow_but_works():
    world = World()
    events = EventBus()
    actor = _make_actor(world)
    mine = world.create_entity("Mine")
    mine.add_component(Harvestable(resource_type="stone", amount=20.0, max_amount=20.0,
                                    required_tool="pickaxe", on_depleted="regen"))

    perform_harvest(world, CONFIG, events, "Actor", "Mine", dt_hours=1.0)

    assert actor.get_component(Inventory).items["stone"] > 0
    no_tool_amount = actor.get_component(Inventory).items["stone"]

    # Same setup, but with the tool: strictly more yield for the same time.
    world2 = World()
    events2 = EventBus()
    actor2 = _make_actor(world2, tools={"pickaxe": 1})
    mine2 = world2.create_entity("Mine")
    mine2.add_component(Harvestable(resource_type="stone", amount=20.0, max_amount=20.0,
                                     required_tool="pickaxe", on_depleted="regen"))
    perform_harvest(world2, CONFIG, events2, "Actor", "Mine", dt_hours=1.0)
    with_tool_amount = actor2.get_component(Inventory).items["stone"]

    assert with_tool_amount > no_tool_amount


def test_felling_a_tree_removes_it_and_may_drop_a_seed():
    world = World()
    events = EventBus()
    actor = _make_actor(world, tools={"axe": 1})
    tree = world.create_entity("Tree")
    tree.add_component(Growth(stage="mature"))
    tree.add_component(Harvestable(resource_type="wood", amount=1.0, max_amount=6.0,
                                    required_tool="axe", on_depleted="remove"))

    perform_harvest(world, CONFIG, events, "Actor", "Tree", dt_hours=1.0)

    assert world.get_entity_by_name("Tree") is None
    assert actor.get_component(Inventory).items.get("wood", 0) > 0


def test_sapling_cannot_be_harvested_yet():
    world = World()
    events = EventBus()
    actor = _make_actor(world, tools={"axe": 1})
    sapling = world.create_entity("Sapling")
    sapling.add_component(Growth(stage="sapling"))
    sapling.add_component(Harvestable(resource_type="wood", amount=0.0, max_amount=6.0,
                                       required_tool="axe", on_depleted="remove"))

    perform_harvest(world, CONFIG, events, "Actor", "Sapling", dt_hours=1.0)

    assert world.get_entity_by_name("Sapling") is not None
    assert actor.get_component(Inventory).items.get("wood", 0) == 0


def test_mine_regenerates_and_restores_its_visual():
    world = World()
    mine = world.create_entity("Mine")
    mine.add_component(Harvestable(
        resource_type="stone", amount=0.0, max_amount=20.0,
        regen_per_hour=5.0, on_depleted="regen", depleted_kind="empty_mine", full_kind="mine",
    ))
    mine.add_component(Renderable(kind="empty_mine"))
    mine.add_component(Position(x=0, y=0))

    system = ResourceRegenSystem()
    events = EventBus()
    system.update(world, CONFIG, events, dt=1.0)

    harvestable = mine.get_component(Harvestable)
    assert harvestable.amount == 5.0
    assert mine.get_component(Renderable).kind == "mine"
