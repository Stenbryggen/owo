from dataclasses import dataclass

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("position")
@dataclass
class Position(Component):
    x: float = 0.0
    y: float = 0.0
