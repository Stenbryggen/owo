from pathlib import Path

from src.owo.components.energy import Energy
from src.owo.core.engine import SimulationEngine

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "world.json"
CONTENT_DIR = REPO_ROOT / "content" / "entities"
RECIPES_DIR = REPO_ROOT / "content" / "recipes"
RESOURCE_TYPES_DIR = REPO_ROOT / "content" / "resource_types"
STARTING_RESOURCES_PATH = REPO_ROOT / "content" / "starting_resources.json"


def build_default_engine() -> SimulationEngine:
    """Build the engine from the repo's default config/content. Shared by the
    CLI demo below and the graphics frontend (src/frontend/) so both start
    from the same world."""
    return SimulationEngine(
        str(CONFIG_PATH), str(CONTENT_DIR), str(RECIPES_DIR), str(RESOURCE_TYPES_DIR),
        str(STARTING_RESOURCES_PATH),
    )


def main():
    print("Initializing AI World Simulator...")
    engine = build_default_engine()

    player = engine.world.get_entity_by_name("Player1")
    birk = engine.world.get_entity_by_name("Birk")

    print(f"Start: Season={engine.current_season}, Time={engine.current_time:.2f}h")

    for i in range(48):
        engine.update(1.0)  # 1 hour step
        if i % 12 == 0:
            p_energy = player.get_component(Energy).current
            b_energy = birk.get_component(Energy).current
            print(
                f"Hour {i}: Season={engine.current_season}, "
                f"Player Energy={p_energy:.2f}, Birk Energy={b_energy:.2f}"
            )

    print("Simulation complete.")


if __name__ == "__main__":
    main()
