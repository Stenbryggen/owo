from src.owo.components import energy, health, sleep  # noqa: F401 - registers components
from src.owo.core.ecs import World
from src.data.save_manager import save_world, load_world


def test_save_and_load_round_trip(tmp_path):
    world = World()
    world.current_time = 5.5
    world.day_count = 12
    world.current_season = "Winter"

    player = world.create_entity("Player1")
    player.add_component(energy.Energy(current=42.0, max_energy=100.0))
    player.add_component(health.Health(is_sick=True))
    player.add_component(sleep.Sleep(is_sleeping=True, recovery_rate=3.0))

    save_path = tmp_path / "save.json"
    save_world(world, str(save_path))

    reloaded = load_world(str(save_path))

    assert reloaded.current_time == 5.5
    assert reloaded.day_count == 12
    assert reloaded.current_season == "Winter"

    reloaded_player = next(e for e in reloaded.entities.values() if e.name == "Player1")
    assert reloaded_player.get_component(energy.Energy).current == 42.0
    assert reloaded_player.get_component(health.Health).is_sick is True
    assert reloaded_player.get_component(sleep.Sleep).recovery_rate == 3.0


def test_save_creates_parent_directories(tmp_path):
    world = World()
    world.current_season = "Spring"

    save_path = tmp_path / "nested" / "dir" / "save.json"
    save_world(world, str(save_path))

    assert save_path.exists()
