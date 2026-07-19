import dataclasses
from typing import Any

from src.owo.core.ecs import Entity, World
from src.owo.core.registry import component_registry, get_component_class


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


def world_to_dict(world: World) -> dict:
    return {
        "current_time": world.current_time,
        "day_count": world.day_count,
        "current_season": world.current_season,
        "entities": [entity_to_dict(entity) for entity in world.entities.values()],
    }


def world_from_dict(data: dict) -> World:
    world = World()
    world.current_time = data.get("current_time", 0.0)
    world.day_count = data.get("day_count", 0)
    world.current_season = data.get("current_season")
    for entity_data in data.get("entities", []):
        entity_from_dict(entity_data, world)
    return world
