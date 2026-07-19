from src.owo.components import energy, health, sleep  # noqa: F401 - registers components
from src.owo.core.ecs import World
from src.owo.core.terrain import Terrain
from src.data.save_manager import load_world, save_world


def test_save_and_load_round_trip(tmp_path):
    world = World()
    world.current_time = 5.5
    world.day_count = 12
    world.current_season = "Winter"

    player = world.create_entity("Player1")
    player.add_component(energy.Energy(current=42.0, max_energy=100.0))
    player.add_component(health.Health(is_sick=True))
    player.add_component(sleep.Sleep(is_sleeping=True, recovery_rate=3.0))

    db_path = tmp_path / "world.db"
    save_world(world, str(db_path))

    reloaded = load_world(str(db_path))

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

    db_path = tmp_path / "nested" / "dir" / "world.db"
    save_world(world, str(db_path))

    assert db_path.exists()


def test_load_returns_none_when_db_file_does_not_exist(tmp_path):
    assert load_world(str(tmp_path / "missing.db")) is None


def test_load_returns_none_for_unknown_slot(tmp_path):
    world = World()
    world.current_season = "Spring"
    db_path = tmp_path / "world.db"
    save_world(world, str(db_path), slot="save1")

    assert load_world(str(db_path), slot="save2") is None


def test_multiple_slots_are_independent(tmp_path):
    db_path = tmp_path / "world.db"

    world_a = World()
    world_a.current_season = "Summer"
    save_world(world_a, str(db_path), slot="a")

    world_b = World()
    world_b.current_season = "Winter"
    save_world(world_b, str(db_path), slot="b")

    assert load_world(str(db_path), slot="a").current_season == "Summer"
    assert load_world(str(db_path), slot="b").current_season == "Winter"


def test_terrain_round_trips_through_sqlite(tmp_path):
    world = World()
    world.current_season = "Spring"
    world.terrain = Terrain()
    world.terrain.set(3, 4, "water")
    world.terrain.set(3, 4, "dirt")  # a filled-in lake tile

    db_path = tmp_path / "world.db"
    save_world(world, str(db_path))

    reloaded = load_world(str(db_path))
    assert reloaded.terrain.get(3, 4) == "dirt"


def test_saving_the_same_slot_again_overwrites_it(tmp_path):
    db_path = tmp_path / "world.db"

    world = World()
    world.current_season = "Summer"
    save_world(world, str(db_path))

    world.current_season = "Autumn"
    save_world(world, str(db_path))

    assert load_world(str(db_path)).current_season == "Autumn"
