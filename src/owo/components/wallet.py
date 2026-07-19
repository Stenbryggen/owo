from dataclasses import dataclass

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("wallet")
@dataclass
class Wallet(Component):
    gold: float = 0.0
