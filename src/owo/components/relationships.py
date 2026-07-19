from dataclasses import dataclass, field
from typing import Dict

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("relationships")
@dataclass
class Relationships(Component):
    """Friendship score toward other entities (by name). Usable by both
    players and NPCs - see work.py, which bumps it whenever entities
    co-op on a quest together."""

    friendship: Dict[str, float] = field(default_factory=dict)
