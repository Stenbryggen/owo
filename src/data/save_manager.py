import json
from pathlib import Path

from src.owo.core.ecs import World
from src.owo.core.serialization import world_from_dict, world_to_dict


def save_world(world: World, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(world_to_dict(world), indent=2))


def load_world(path: str) -> World:
    data = json.loads(Path(path).read_text())
    return world_from_dict(data)
