from src.owo.components.harvestable import Harvestable
from src.owo.components.renderable import Renderable
from src.owo.core.registry import register_system
from src.owo.core.systems import System


@register_system("resource_regen")
class ResourceRegenSystem(System):
    """Slowly refills mines (on_depleted == "regen") over time, restoring
    their visual once they're no longer empty. Trees (on_depleted ==
    "remove") never regen here - they're gone once felled, and come back
    only through TreeGrowthSystem's reproduction."""

    required_components = (Harvestable,)

    def update(self, world, config, events, dt):
        for entity in world.get_entities_with_components(Harvestable):
            harvestable = entity.get_component(Harvestable)
            if harvestable.on_depleted != "regen" or harvestable.regen_per_hour <= 0:
                continue
            if harvestable.amount >= harvestable.max_amount:
                continue

            was_empty = harvestable.amount <= 0
            harvestable.amount = min(
                harvestable.max_amount, harvestable.amount + harvestable.regen_per_hour * dt
            )

            if was_empty and harvestable.amount > 0 and harvestable.full_kind:
                renderable = entity.get_component(Renderable)
                if renderable is not None:
                    renderable.kind = harvestable.full_kind
