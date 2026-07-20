import json
import os
import random
from pathlib import Path
from typing import Optional

from src.owo.core import registry
from src.owo.core.ai_provider import get_provider
from src.owo.core.crafting import load_recipes, perform_craft
from src.owo.core.eating import perform_eat
from src.owo.core.ecs import World
from src.owo.core.events import EventBus
from src.owo.core.harvest import perform_harvest
from src.owo.core.planting import perform_plant
from src.owo.core.resource_spawning import spawn_resource
from src.owo.core.resource_types import load_resource_types
from src.owo.core.serialization import entity_from_dict
from src.owo.core.systems import SystemManager
from src.owo.core.terrain import Terrain, carve_lake_with_island, world_to_tile
from src.owo.core.validation import validate_entity_dict
from src.owo.core.work import perform_work
from src.owo.core.worldgen import ensure_chunks_loaded


class SimulationEngine:
    def __init__(
        self, config_path: str, content_dir: str,
        recipes_dir: Optional[str] = None, resource_types_dir: Optional[str] = None,
        starting_resources_path: Optional[str] = None,
    ):
        registry.discover_and_import("src.owo.components")
        registry.discover_and_import("src.owo.systems")

        self.config = self._load_config(config_path)

        self.world = World()
        self.world.current_season = self.config["world"]["seasons"][0]
        self.world.resource_types = load_resource_types(resource_types_dir) if resource_types_dir else {}
        self._setup_terrain()

        self.events = EventBus()
        self.ai_provider = get_provider(self.config)

        system_instances = [
            registry.get_system_class(name)() for name in self.config["systems"]["order"]
        ]
        self.system_manager = SystemManager(system_instances, self.world, self.events, self.ai_provider)

        self._load_content(Path(content_dir))
        if starting_resources_path:
            self._load_starting_resources(Path(starting_resources_path))
        self.recipes = load_recipes(recipes_dir) if recipes_dir else {}

    def _setup_terrain(self) -> None:
        terrain_config = self.config.get("terrain", {})
        self.world.terrain = Terrain()
        carve_lake_with_island(
            self.world.terrain,
            terrain_config.get("lake_col", 3),
            terrain_config.get("lake_row", 13),
            terrain_config.get("lake_radius_tiles", 3),
            terrain_config.get("lake_island_radius_tiles", 1),
        )

        # Mark the hand-placed starting area as already generated, so the
        # procedural generator never scatters trees/mines on top of the
        # curated content entities - it only kicks in once players wander
        # beyond this radius. See core/worldgen.py.
        worldgen_config = self.config.get("worldgen", {})
        starting_radius = worldgen_config.get("starting_chunk_radius", 2)
        for cx in range(-starting_radius, starting_radius + 1):
            for cy in range(-starting_radius, starting_radius + 1):
                self.world.loaded_chunks.add((cx, cy))

        # A new world gets a random seed (a different world every game);
        # config can still pin one down for reproducible testing. A world
        # loaded from a save overwrites this via World.reset_from(), so
        # exploring further after a reload keeps using the seed that
        # world's already-generated chunks were made with.
        self.world.worldgen_seed = worldgen_config.get("seed") or random.randint(0, 2**31 - 1)

    def ensure_chunks_loaded(self, x: float, y: float) -> None:
        worldgen_config = self.config.get("worldgen", {})
        ensure_chunks_loaded(
            self.world, x, y,
            radius_chunks=worldgen_config.get("load_radius_chunks", 2),
            base_seed=self.world.worldgen_seed,
            chunk_size=worldgen_config.get("chunk_size", 16),
        )

    def fill_terrain_tile(self, x: float, y: float) -> bool:
        """Permanently fills a water tile at world position (x, y) with
        dirt. Returns False if that tile wasn't water."""
        col, row = world_to_tile(x, y)
        if self.world.terrain.get(col, row) != "water":
            return False
        self.world.terrain.set(col, row, "dirt")
        self.events.publish("terrain_filled", {"col": col, "row": row})
        return True

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

    def _load_starting_resources(self, path: Path) -> None:
        """Hand-placed resource nodes (the starting trees, mines, ...),
        spawned through the exact same spawn_resource() worldgen uses -
        their properties live only in content/resource_types/*.json, never
        duplicated here. Just position + which resource type + a stable
        name (so quests/tests can keep referring to e.g. "Tree1")."""
        entries = json.loads(path.read_text())
        for entry in entries:
            resource_type = self.world.resource_types[entry["resource_type"]]
            spawn_resource(
                self.world, entry["x"], entry["y"], resource_type,
                mature=entry.get("mature", True), name=entry.get("name"),
            )

    def update(self, delta_time_hours: float) -> None:
        self.system_manager.update(self.world, self.config, delta_time_hours)

    def perform_work(self, actor_name: str, quest_name: str, delta_time_hours: float) -> None:
        perform_work(self.world, self.config, self.events, actor_name, quest_name, delta_time_hours)

    def perform_harvest(self, actor_name: str, resource_name: str, delta_time_hours: float) -> None:
        perform_harvest(self.world, self.config, self.events, actor_name, resource_name, delta_time_hours)

    def perform_plant(self, actor_name: str) -> bool:
        return perform_plant(self.world, self.events, actor_name)

    def perform_craft(self, actor_name: str, recipe_name: str) -> bool:
        return perform_craft(self.world, self.events, self.recipes, actor_name, recipe_name)

    def perform_eat(self, actor_name: str) -> bool:
        return perform_eat(self.world, self.events, actor_name)

    @property
    def current_time(self) -> float:
        return self.world.current_time

    @property
    def current_season(self) -> str:
        return self.world.current_season

    @property
    def day_count(self) -> int:
        return self.world.day_count
