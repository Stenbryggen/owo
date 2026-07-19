from dataclasses import dataclass

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("thermal")
@dataclass
class Thermal(Component):
    insulation: float = 0.0
    heat_source: float = 0.0
