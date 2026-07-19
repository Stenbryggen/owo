from dataclasses import dataclass

from src.owo.core.ecs import Component
from src.owo.core.registry import register_component


@register_component("renderable")
@dataclass
class Renderable(Component):
    """Marks a static, non-living world prop and how the frontend should
    draw it. New prop types (new `kind` values) are added purely as content
    - drop a new content/entities/*.json file with a `kind` the renderer
    recognizes (or falls back to a generic shape for)."""

    kind: str = "prop"
