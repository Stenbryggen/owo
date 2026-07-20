import random

from src.owo.components.growth import Growth
from src.owo.components.harvestable import Harvestable
from src.owo.components.inventory import Inventory
from src.owo.components.renderable import Renderable
from src.owo.components.skills import Skills
from src.owo.core.skills import skill_efficiency, skill_level

BASE_HARVEST_PER_HOUR = 4.0
NO_TOOL_PENALTY = 0.25  # harvestable, just much slower without the right tool - not impossible.
# Realistic bootstrapping: you can gather a little wood by hand to craft a
# first axe, rather than being hard-blocked with nothing in your inventory.
SEED_DROP_CHANCE = 0.4
NUT_DROP_CHANCE = 0.3


def _has_tool(inventory: Inventory, tool_name: str) -> bool:
    return bool(tool_name) and inventory.items.get(tool_name, 0) >= 1


def perform_harvest(world, config, events, actor_name: str, resource_name: str, dt_hours: float) -> None:
    """One entity spends dt_hours harvesting one resource node. On-demand
    action (not a per-tick System), same pattern as perform_work."""
    if dt_hours <= 0:
        return

    actor = world.get_entity_by_name(actor_name)
    resource_entity = world.get_entity_by_name(resource_name)
    if actor is None or resource_entity is None:
        return

    harvestable = resource_entity.get_component(Harvestable)
    if harvestable is None or harvestable.amount <= 0:
        return

    growth = resource_entity.get_component(Growth)
    if growth is not None and growth.stage != "mature":
        return  # not grown enough to harvest yet

    inventory = actor.get_component(Inventory)
    if inventory is None:
        return

    skills = actor.get_component(Skills)
    level = skill_level(skills, harvestable.resource_type) if skills else 1
    efficiency = skill_efficiency(level)
    tool_multiplier = 1.0 if not harvestable.required_tool else (
        1.0 if _has_tool(inventory, harvestable.required_tool) else NO_TOOL_PENALTY
    )

    yield_amount = min(
        harvestable.amount,
        BASE_HARVEST_PER_HOUR * efficiency * tool_multiplier * dt_hours,
    )
    harvestable.amount -= yield_amount
    inventory.items[harvestable.resource_type] = (
        inventory.items.get(harvestable.resource_type, 0.0) + yield_amount
    )

    events.publish(
        "resource_harvested",
        {"entity": actor_name, "resource": resource_name,
         "item": harvestable.resource_type, "amount": yield_amount},
    )

    if harvestable.amount <= 0:
        _deplete(world, events, resource_entity, harvestable, growth, inventory)


def _deplete(world, events, resource_entity, harvestable: Harvestable, growth, inventory: Inventory) -> None:
    if harvestable.on_depleted == "remove":
        if growth is not None and random.random() < SEED_DROP_CHANCE:
            inventory.items["seed"] = inventory.items.get("seed", 0.0) + 1
            events.publish("seed_dropped", {"resource": resource_entity.name})
        if growth is not None and random.random() < NUT_DROP_CHANCE:
            inventory.items["nuts"] = inventory.items.get("nuts", 0.0) + 1
            events.publish("nuts_dropped", {"resource": resource_entity.name})
        world.entities.pop(resource_entity.id, None)
        events.publish("resource_removed", {"resource": resource_entity.name})
    elif harvestable.on_depleted == "regen":
        renderable = resource_entity.get_component(Renderable)
        if renderable is not None and harvestable.depleted_kind:
            renderable.kind = harvestable.depleted_kind
        events.publish("resource_depleted", {"resource": resource_entity.name})
