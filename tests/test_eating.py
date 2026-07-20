from pathlib import Path

from src.owo.components.energy import Energy
from src.owo.components.inventory import Inventory
from src.owo.core.eating import perform_eat
from src.owo.core.ecs import World
from src.owo.core.events import EventBus
from src.owo.core.resource_types import load_resource_types

REPO_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_TYPES_DIR = REPO_ROOT / "content" / "resource_types"


def _make_world():
    world = World()
    world.resource_types = load_resource_types(str(RESOURCE_TYPES_DIR))
    return world


def test_eating_restores_energy_and_consumes_one_food():
    world = _make_world()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Energy(current=50.0, max_energy=100.0))
    actor.add_component(Inventory(items={"berries": 2}))

    assert perform_eat(world, events, "Actor") is True

    assert actor.get_component(Energy).current == 58.0  # +8 for berries
    assert actor.get_component(Inventory).items["berries"] == 1


def test_eating_picks_the_most_restorative_food_available():
    world = _make_world()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Energy(current=50.0, max_energy=100.0))
    actor.add_component(Inventory(items={"berries": 1, "fish": 1}))

    perform_eat(world, events, "Actor")

    inventory = actor.get_component(Inventory)
    assert "fish" not in inventory.items  # fish (highest restore) eaten first
    assert inventory.items["berries"] == 1


def test_eating_caps_at_max_energy():
    world = _make_world()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Energy(current=95.0, max_energy=100.0))
    actor.add_component(Inventory(items={"fish": 1}))

    perform_eat(world, events, "Actor")

    assert actor.get_component(Energy).current == 100.0


def test_eating_with_no_food_fails():
    world = _make_world()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Energy(current=50.0, max_energy=100.0))
    actor.add_component(Inventory(items={"wood": 5}))

    assert perform_eat(world, events, "Actor") is False
    assert actor.get_component(Energy).current == 50.0


def test_eating_publishes_food_eaten_event():
    world = _make_world()
    events = EventBus()
    fired = []
    events.subscribe("food_eaten", lambda p: fired.append(p))

    actor = world.create_entity("Actor")
    actor.add_component(Energy(current=50.0, max_energy=100.0))
    actor.add_component(Inventory(items={"nuts": 1}))

    perform_eat(world, events, "Actor")

    assert fired == [{"entity": "Actor", "food": "nuts", "energy_restored": 12.0}]


def test_cooked_fish_restores_more_energy_than_raw_fish():
    world = _make_world()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Energy(current=0.0, max_energy=100.0))
    actor.add_component(Inventory(items={"fish": 1, "cooked_fish": 1}))

    perform_eat(world, events, "Actor")

    # cooked_fish (higher food_energy) is preferred over raw fish
    assert "cooked_fish" not in actor.get_component(Inventory).items
    assert actor.get_component(Inventory).items["fish"] == 1
    assert actor.get_component(Energy).current > 20.0  # more than raw fish alone would give
