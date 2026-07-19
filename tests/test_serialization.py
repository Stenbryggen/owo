from src.owo.components import energy, health, thermal, sleep  # noqa: F401 - registers components
from src.owo.core.ecs import World
from src.owo.core.serialization import entity_to_dict, entity_from_dict


def test_round_trip_energy_component():
    world = World()
    entity = world.create_entity("Player1")
    entity.add_component(energy.Energy(current=42.0, max_energy=100.0))

    data = entity_to_dict(entity)
    rebuilt = entity_from_dict(data, World())

    assert rebuilt.name == "Player1"
    rebuilt_energy = rebuilt.get_component(energy.Energy)
    assert rebuilt_energy.current == 42.0
    assert rebuilt_energy.max_energy == 100.0


def test_round_trip_all_registered_components():
    world = World()
    entity = world.create_entity("Multi")
    entity.add_component(energy.Energy())
    entity.add_component(health.Health(is_sick=True))
    entity.add_component(thermal.Thermal(heat_source=5.0))
    entity.add_component(sleep.Sleep(is_sleeping=True, recovery_rate=3.0))

    data = entity_to_dict(entity)
    assert {c["type"] for c in data["components"]} == {"energy", "health", "thermal", "sleep"}

    rebuilt = entity_from_dict(data, World())
    assert rebuilt.get_component(health.Health).is_sick is True
    assert rebuilt.get_component(sleep.Sleep).recovery_rate == 3.0
