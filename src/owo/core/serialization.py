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
