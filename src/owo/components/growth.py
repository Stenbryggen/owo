from dataclasses import dataclass

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("growth")
@dataclass
class Growth(Component):
    stage: str = "sapling"  # sapling -> mature
    age_days: int = 0
    mature_at_days: int = 3
    reproduction_chance: float = 0.15  # per day, once mature
