from dataclasses import dataclass, field
from typing import Dict

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("inventory")
@dataclass
class Inventory(Component):
    items: Dict[str, float] = field(default_factory=dict)
