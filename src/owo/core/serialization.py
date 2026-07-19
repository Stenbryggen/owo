import dataclasses
from typing import Any

from src.owo.core.ecs import Entity, World
from src.owo.core.registry import component_registry, get_component_class
from src.owo.core.terrain import Terrain


def component_to_dict(component: Any) -> dict:
    return dataclasses.asdict(component)


def component_type_name(component: Any) -> str:
    for name, cls in component_registry().items():
        if type(component) is cls:
            return name
    raise ValueError(f"Component type {type(component)!r} is not registered")


def entity_to_dict(entity: Entity) -> dict:
    return {
        "name": entity.name,
        "components": [
            {"type": component_type_name(component), "params": component_to_dict(component)}
            for component in entity.components.values()
        ],
    }


def entity_from_dict(data: dict, world: World) -> Entity:
    entity = world.create_entity(data.get("name"))
    for component_data in data.get("components", []):
        cls = get_component_class(component_data["type"])
        entity.add_component(cls(**component_data.get("params", {})))
    return entity


def terrain_to_dict(terrain: Terrain) -> dict:
    return {
        "default": terrain.default,
        "tiles": {f"{col},{row}": tile_type for (col, row), tile_type in terrain.tiles.items()},
    }


def terrain_from_dict(data: dict) -> Terrain:
    terrain = Terrain(data.get("default", "grass"))
    for key, tile_type in data.get("tiles", {}).items():
        col, row = (int(part) for part in key.split(","))
        terrain.tiles[(col, row)] = tile_type
    return terrain


def world_to_dict(world: World) -> dict:
    return {
        "current_time": world.current_time,
        "day_count": world.day_count,
        "current_season": world.current_season,
        "terrain": terrain_to_dict(world.terrain) if world.terrain else None,
        "loaded_chunks": [list(chunk) for chunk in world.loaded_chunks],
        "entities": [entity_to_dict(entity) for entity in world.entities.values()],
    }


def world_from_dict(data: dict) -> World:
    world = World()
    world.current_time = data.get("current_time", 0.0)
    world.day_count = data.get("day_count", 0)
    world.current_season = data.get("current_season")
    if data.get("terrain"):
        world.terrain = terrain_from_dict(data["terrain"])
    world.loaded_chunks = {tuple(chunk) for chunk in data.get("loaded_chunks", [])}
    for entity_data in data.get("entities", []):
        entity_from_dict(entity_data, world)
    return world
