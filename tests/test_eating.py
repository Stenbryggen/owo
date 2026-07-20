from src.owo.components.energy import Energy
from src.owo.components.inventory import Inventory
from src.owo.core.eating import perform_eat
from src.owo.core.ecs import World
from src.owo.core.events import EventBus


def test_eating_restores_energy_and_consumes_one_food():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Energy(current=50.0, max_energy=100.0))
    actor.add_component(Inventory(items={"berries": 2}))

    assert perform_eat(world, events, "Actor") is True

    assert actor.get_component(Energy).current == 58.0  # +8 for berries
    assert actor.get_component(Inventory).items["berries"] == 1


def test_eating_picks_the_most_restorative_food_available():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Energy(current=50.0, max_energy=100.0))
    actor.add_component(Inventory(items={"berries": 1, "fish": 1}))

    perform_eat(world, events, "Actor")

    inventory = actor.get_component(Inventory)
    assert "fish" not in inventory.items  # fish (highest restore) eaten first
    assert inventory.items["berries"] == 1


def test_eating_caps_at_max_energy():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Energy(current=95.0, max_energy=100.0))
    actor.add_component(Inventory(items={"fish": 1}))

    perform_eat(world, events, "Actor")

    assert actor.get_component(Energy).current == 100.0


def test_eating_with_no_food_fails():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Energy(current=50.0, max_energy=100.0))
    actor.add_component(Inventory(items={"wood": 5}))

    assert perform_eat(world, events, "Actor") is False
    assert actor.get_component(Energy).current == 50.0


def test_eating_publishes_food_eaten_event():
    world = World()
    events = EventBus()
    fired = []
    events.subscribe("food_eaten", lambda p: fired.append(p))

    actor = world.create_entity("Actor")
    actor.add_component(Energy(current=50.0, max_energy=100.0))
    actor.add_component(Inventory(items={"nuts": 1}))

    perform_eat(world, events, "Actor")

    assert fired == [{"entity": "Actor", "food": "nuts", "energy_restored": 12.0}]
