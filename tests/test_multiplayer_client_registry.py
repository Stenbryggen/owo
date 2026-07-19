import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Regression test for a real bug: the network client never builds a
# SimulationEngine (only src/main.py's build_default_engine() and
# GameServer do, via SimulationEngine.__init__ calling
# registry.discover_and_import), so nothing guaranteed every component
# module (e.g. motion.py, only ever imported indirectly) got registered
# before world_from_dict() tried to deserialize a snapshot containing one.
# Must run in a fresh subprocess - in the normal test process, other tests
# have already imported every component module, which would hide the bug.
_SCRIPT = """
import src.frontend.network_client  # noqa: F401 - must register every component as a side effect
from src.owo.core.serialization import world_from_dict

payload = {
    "current_time": 0.0, "day_count": 0, "current_season": "Spring", "terrain": None,
    "entities": [
        {"name": "TestCart", "components": [
            {"type": "position", "params": {"x": 0.0, "y": 0.0}},
            {"type": "motion", "params": {"speed_bonus": 0.5}},
        ]},
    ],
}
world = world_from_dict(payload)
assert world.get_entity_by_name("TestCart") is not None
print("OK")
"""


def test_network_client_can_deserialize_every_component_type():
    result = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout
