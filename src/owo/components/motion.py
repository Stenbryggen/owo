from dataclasses import dataclass

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("motion")
@dataclass
class Motion(Component):
    """Missing component = no effect (implicit 0), per the doc's
    component-based design. A prop with this (a cart, boots, ...) boosts
    the speed of anyone standing near it - see core/movement.py."""

    speed_bonus: float = 0.0
