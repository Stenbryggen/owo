from pathlib import Path

from src.owo.components.energy import Energy
from src.owo.components.sleep import Sleep
from src.owo.core.engine import SimulationEngine

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "world.json"
CONTENT_DIR = REPO_ROOT / "content" / "entities"


def build_engine() -> SimulationEngine:
    return SimulationEngine(str(CONFIG_PATH), str(CONTENT_DIR))


def get_entity(engine, name):
    return next(e for e in engine.world.entities.values() if e.name == name)


def test_loads_all_content_entities():
    engine = build_engine()
    names = {e.name for e in engine.world.entities.values()}
    assert names == {
        "Player1", "Birk", "Campfire",
        "Tree1", "Tree2", "Tree3", "Tree4",
        "Mine1", "Mine2", "QuestBoard", "Chest",
        "QuestGatherWood", "QuestClearRocks", "Cart",
    }


def test_energy_drains_over_time_for_non_sleeping_entity():
    engine = build_engine()
    birk = get_entity(engine, "Birk")
    start_energy = birk.get_component(Energy).current

    for _ in range(10):
        engine.update(1.0)

    assert birk.get_component(Energy).current < start_energy


def test_sleeping_player_gains_energy_overnight_then_wakes_and_drains():
    engine = build_engine()
    player = get_entity(engine, "Player1")
    start_energy = player.get_component(Energy).current

    # Spring night is 12h; running through it should net-recover energy
    # (drain -1.1/h vs recovery +5/h) and end sleep once day starts.
    for _ in range(12):
        engine.update(1.0)

    energy_after_night = player.get_component(Energy).current
    assert energy_after_night > start_energy
    assert player.get_component(Sleep).is_sleeping is False

    for _ in range(12):
        engine.update(1.0)

    assert player.get_component(Energy).current < energy_after_night


def test_season_changes_after_thirty_days():
    engine = build_engine()
    assert engine.current_season == "Spring"

    for _ in range(30 * 24):
        engine.update(1.0)

    assert engine.day_count == 30
    assert engine.current_season == "Summer"


def test_fresh_engines_get_different_random_worldgen_seeds():
    engine_a = build_engine()
    engine_b = build_engine()

    assert engine_a.world.worldgen_seed is not None
    assert engine_a.world.worldgen_seed != engine_b.world.worldgen_seed
