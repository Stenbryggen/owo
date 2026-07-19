from dataclasses import dataclass

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("energy")
@dataclass
class Energy(Component):
    current: float = 100.0
    max_energy: float = 100.0
