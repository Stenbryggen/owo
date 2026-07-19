import uuid
from typing import Dict, List, Type, Any


class Component:
    """Marker base class for all components. Concrete components are dataclasses."""
    pass


class Entity:
    def __init__(self, name: str = None):
        self.id = uuid.uuid4()
        self.name = name or str(self.id)
        self.components: Dict[Type[Component], Component] = {}

    def add_component(self, component: Component):
        self.components[type(component)] = component
        return self

    def get_component(self, component_type: Type[Component]) -> Any:
        return self.components.get(component_type)

    def has_component(self, component_type: Type[Component]) -> bool:
        return component_type in self.components


class World:
    def __init__(self):
        self.entities: Dict[uuid.UUID, Entity] = {}
        # Global simulation clock, owned by the time_season system. Not an
        # ECS component since it describes the world itself, not an entity.
        self.current_time: float = 0.0
        self.day_count: int = 0
        self.current_season: str = None

    def create_entity(self, name: str = None) -> Entity:
        entity = Entity(name)
        self.entities[entity.id] = entity
        return entity

    def get_entities_with_components(self, *component_types: Type[Component]) -> List[Entity]:
        return [
            e for e in self.entities.values()
            if all(e.has_component(ct) for ct in component_types)
        ]
