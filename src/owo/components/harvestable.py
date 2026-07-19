from dataclasses import dataclass

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("harvestable")
@dataclass
class Harvestable(Component):
    resource_type: str = "wood"  # item name granted per unit harvested
    amount: float = 10.0
    max_amount: float = 10.0
    regen_per_hour: float = 0.0  # mines slowly regenerate; trees don't (0)
    required_tool: str = ""  # empty = no tool required, just slower without one
    on_depleted: str = "remove"  # "remove" (trees: felled, gone) | "regen" (mines: empties out, refills)
    depleted_kind: str = ""  # Renderable.kind to show while empty, only used by "regen"
    full_kind: str = ""  # Renderable.kind to restore once regenerated back above 0
