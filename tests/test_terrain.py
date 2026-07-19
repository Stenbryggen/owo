from pathlib import Path

from src.owo.core.engine import SimulationEngine
from src.owo.core.serialization import world_from_dict, world_to_dict
from src.owo.core.terrain import Terrain, carve_lake_with_island, world_to_tile

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "world.json"
CONTENT_DIR = REPO_ROOT / "content" / "entities"


def test_unset_tile_returns_default():
    terrain = Terrain()
    assert terrain.get(5, 5) == "grass"


def test_set_and_get_override():
    terrain = Terrain()
    terrain.set(5, 5, "water")
    assert terrain.get(5, 5) == "water"


def test_setting_back_to_default_clears_the_override():
    terrain = Terrain()
    terrain.set(5, 5, "water")
    terrain.set(5, 5, "grass")
    assert terrain.get(5, 5) == "grass"
    assert (5, 5) not in terrain.tiles  # sparse: default tiles cost nothing


def test_world_to_tile():
    assert world_to_tile(0, 0, tile_size=80) == (0, 0)
    assert world_to_tile(85, 165, tile_size=80) == (1, 2)


def test_carve_lake_with_island_leaves_center_at_default():
    terrain = Terrain()
    carve_lake_with_island(terrain, center_col=10, center_row=10, radius_tiles=3, island_radius_tiles=1)

    assert terrain.get(10, 10) == "grass"  # island center
    assert terrain.get(13, 10) == "water"  # within lake radius, outside island
    assert terrain.get(19, 19) == "grass"  # far outside the lake


def test_engine_carves_the_default_lake():
    engine = SimulationEngine(str(CONFIG_PATH), str(CONTENT_DIR))
    terrain = engine.world.terrain

    assert terrain is not None
    assert any(t == "water" for t in terrain.tiles.values())


def test_fill_terrain_tile_converts_water_to_dirt_and_publishes_event():
    engine = SimulationEngine(str(CONFIG_PATH), str(CONTENT_DIR))
    fired = []
    engine.events.subscribe("terrain_filled", lambda p: fired.append(p))

    col, row = next(
        (c, r) for (c, r), t in engine.world.terrain.tiles.items() if t == "water"
    )
    x, y = col * 80 + 1, row * 80 + 1

    assert engine.fill_terrain_tile(x, y) is True
    assert engine.world.terrain.get(col, row) == "dirt"
    assert fired == [{"col": col, "row": row}]


def test_fill_terrain_tile_on_non_water_does_nothing():
    engine = SimulationEngine(str(CONFIG_PATH), str(CONTENT_DIR))
    # Player1's starting position is on dry land per content/entities/player.json
    assert engine.fill_terrain_tile(900, 800) is False


def test_terrain_round_trips_through_save_and_load():
    engine = SimulationEngine(str(CONFIG_PATH), str(CONTENT_DIR))
    col, row = next(
        (c, r) for (c, r), t in engine.world.terrain.tiles.items() if t == "water"
    )
    engine.fill_terrain_tile(col * 80 + 1, row * 80 + 1)

    reloaded = world_from_dict(world_to_dict(engine.world))

    assert reloaded.terrain.get(col, row) == "dirt"
