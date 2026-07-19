from pathlib import Path

from src.owo.components.energy import Energy
from src.owo.core.engine import SimulationEngine

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "world.json"
CONTENT_DIR = REPO_ROOT / "content" / "entities"


def main():
    print("Initializing AI World Simulator...")
    engine = SimulationEngine(str(CONFIG_PATH), str(CONTENT_DIR))

    player = next(e for e in engine.world.entities.values() if e.name == "Player1")
    birk = next(e for e in engine.world.entities.values() if e.name == "Birk")

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
