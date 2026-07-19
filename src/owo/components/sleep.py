from dataclasses import dataclass
from typing import Optional

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("sleep")
@dataclass
class Sleep(Component):
    is_sleeping: bool = False
    recovery_rate: Optional[float] = None
