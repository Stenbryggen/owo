from dataclasses import dataclass

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("npc_profile")
@dataclass
class NpcProfile(Component):
    """Marks an entity as an autonomous NPC and holds what its daily AI
    decision (see systems/npc_autonomy.py) acts on and updates."""

    occupation: str = ""
    current_goal: str = ""
