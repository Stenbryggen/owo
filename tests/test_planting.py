from src.owo.components.growth import Growth
from src.owo.components.inventory import Inventory
from src.owo.components.position import Position
from src.owo.core.ecs import World
from src.owo.core.events import EventBus
from src.owo.core.planting import perform_plant


def test_planting_consumes_a_seed_and_spawns_a_sapling():
    world = World()
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
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Position(x=0, y=0))
    actor.add_component(Inventory(items={}))

    assert perform_plant(world, events, "Actor") is False
    assert not any(e.get_component(Growth) is not None for e in world.entities.values())
