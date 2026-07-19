from dataclasses import dataclass, field
from typing import Dict

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("skills")
@dataclass
class Skills(Component):
    levels: Dict[str, int] = field(default_factory=dict)
    xp: Dict[str, float] = field(default_factory=dict)
