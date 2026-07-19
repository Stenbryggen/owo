import json
import os
from pathlib import Path

from src.owo.core import registry
from src.owo.core.ai_provider import get_provider
from src.owo.core.ecs import World
from src.owo.core.events import EventBus
from src.owo.core.serialization import entity_from_dict
from src.owo.core.systems import SystemManager
from src.owo.core.validation import validate_entity_dict


class SimulationEngine:
    def __init__(self, config_path: str, content_dir: str):
        registry.discover_and_import("src.owo.components")
        registry.discover_and_import("src.owo.systems")

        self.config = self._load_config(config_path)

        self.world = World()
        self.world.current_season = self.config["world"]["seasons"][0]

        self.events = EventBus()
        system_instances = [
            registry.get_system_class(name)() for name in self.config["systems"]["order"]
        ]
        self.system_manager = SystemManager(system_instances, self.events)

        self.ai_provider = get_provider(self.config.get("ai_provider", "stub"))

        self._load_content(Path(content_dir))

    def _load_config(self, path: str) -> dict:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found at {path}")
        with open(path, "r") as f:
            return json.load(f)

    def _load_content(self, content_dir: Path) -> None:
        for path in sorted(content_dir.glob("*.json")):
            with open(path, "r") as f:
                data = json.load(f)
            validate_entity_dict(data)
            entity_from_dict(data, self.world)

    def update(self, delta_time_hours: float) -> None:
        self.system_manager.update(self.world, self.config, delta_time_hours)

    @property
    def current_time(self) -> float:
        return self.world.current_time

    @property
    def current_season(self) -> str:
        return self.world.current_season

    @property
    def day_count(self) -> int:
        return self.world.day_count
