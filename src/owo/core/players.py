import json
from pathlib import Path

from src.owo.core.ecs import Entity, World
from src.owo.core.serialization import entity_from_dict


def spawn_player(world: World, template_path: str, name: str, spawn_index: int = 0) -> Entity:
    """Clones the player content template with a new name for a newly
    connected client, offsetting its start position so simultaneous
    players don't spawn stacked on top of each other."""
    data = json.loads(Path(template_path).read_text())
    data["name"] = name

    for component in data.get("components", []):
        if component["type"] == "position":
            component["params"]["x"] += (spawn_index % 4) * 70
            component["params"]["y"] += (spawn_index // 4) * 70

    return entity_from_dict(data, world)
