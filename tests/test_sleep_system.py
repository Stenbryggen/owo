from src.owo.components.energy import Energy
from src.owo.components.sleep import Sleep
from src.owo.core.ecs import World
from src.owo.core.events import EventBus
from src.owo.systems.sleep_recovery import SleepRecoverySystem

CONFIG = {
    "world": {
        "seasonal_factors": {
            "Summer": {"night_length_hours": 8},
        },
    },
    "player_base_stats": {"recovery_rate_base": 5.0},
}


def make_world(current_time: float) -> World:
    world = World()
    world.current_season = "Summer"
    world.current_time = current_time
    return world


def test_recovers_energy_while_sleeping_at_night():
    world = make_world(current_time=2.0)
    entity = world.create_entity("Sleeper")
    entity.add_component(Energy(current=50.0, max_energy=100.0))
    entity.add_component(Sleep(is_sleeping=True))
    events = EventBus()
    published = []
    events.subscribe("sleep_recovery_applied", lambda p: published.append(p))

    SleepRecoverySystem().update(world, CONFIG, events, dt=1.0)

    assert entity.get_component(Energy).current == 55.0
    assert entity.get_component(Sleep).is_sleeping is True
    assert published == [{"entity": "Sleeper", "amount": 5.0}]


def test_energy_capped_at_max_while_sleeping():
    world = make_world(current_time=2.0)
    entity = world.create_entity("Sleeper")
    entity.add_component(Energy(current=98.0, max_energy=100.0))
    entity.add_component(Sleep(is_sleeping=True))

    SleepRecoverySystem().update(world, CONFIG, EventBus(), dt=1.0)

    assert entity.get_component(Energy).current == 100.0


def test_custom_recovery_rate_overrides_base():
    world = make_world(current_time=2.0)
    entity = world.create_entity("Sleeper")
    entity.add_component(Energy(current=50.0, max_energy=100.0))
    entity.add_component(Sleep(is_sleeping=True, recovery_rate=1.0))

    SleepRecoverySystem().update(world, CONFIG, EventBus(), dt=1.0)

    assert entity.get_component(Energy).current == 51.0


def test_stops_sleeping_and_publishes_sleep_ended_once_day_starts():
    world = make_world(current_time=10.0)  # past Summer's 8h night
    entity = world.create_entity("Sleeper")
    entity.add_component(Energy(current=50.0, max_energy=100.0))
    entity.add_component(Sleep(is_sleeping=True))
    events = EventBus()
    published = []
    events.subscribe("sleep_ended", lambda p: published.append(p))

    SleepRecoverySystem().update(world, CONFIG, events, dt=1.0)

    assert entity.get_component(Sleep).is_sleeping is False
    assert entity.get_component(Energy).current == 50.0
    assert published == [{"entity": "Sleeper"}]


def test_no_effect_when_not_sleeping():
    world = make_world(current_time=2.0)
    entity = world.create_entity("Awake")
    entity.add_component(Energy(current=50.0, max_energy=100.0))
    entity.add_component(Sleep(is_sleeping=False))

    SleepRecoverySystem().update(world, CONFIG, EventBus(), dt=1.0)

    assert entity.get_component(Energy).current == 50.0
