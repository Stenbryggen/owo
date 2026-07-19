from dataclasses import dataclass, field
from typing import Dict

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("quest")
@dataclass
class Quest(Component):
    title: str = ""
    skill: str = "woodcutting"
    effort_required: float = 10.0
    reward_gold: float = 0.0
    reward_xp: float = 0.0
    status: str = "open"  # open -> in_progress -> completed
    # entity name -> effort they've personally contributed. Doubles as the
    # progress log (sum of values) and the co-op roster (its keys) used to
    # decide synergy/master-apprentice bonuses.
    contributors: Dict[str, float] = field(default_factory=dict)
