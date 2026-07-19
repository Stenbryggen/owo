import uuid
from typing import Dict, List, Type, Any

class Component:
    """Base class for all components."""
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

    def create_entity(self, name: str = None) -> Entity:
        entity = Entity(name)
        self.entities[entity.id] = entity
        return entity

    def get_entities_with_components(self, *component_types: Type[Component]) -> List[Entity]:
        return [
            e for e in self.entities.values()
            if all(e.has_component(ct) for ct in component_types)
        ]

# Define some base components mentioned in the architecture
class MotionComponent(Component):
    def __init__(self, speed: float = 0.0):
        self.speed = speed

class ThermalComponent(Component):
    def __init__(self, insulation: float = 0.0, heat_source: float = 0.0):
        self.insulation = insulation
        self.heat_source = heat_source

class EnergyComponent(Component):
    def __init__(self, current: float = 100.0, max_energy: float = 100.0):
        self.current = current
        self.max_energy = max_energy

class HealthComponent(Component):
    def __init__(self, current: float = 100.0, max_health: float = 100.0, is_sick: bool = False):
        self.current = current
        self.max_health = max_health
        self.is_sick = is_sick
