from dataclasses import dataclass

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("health")
@dataclass
class Health(Component):
    current: float = 100.0
    max_health: float = 100.0
    is_sick: bool = False
