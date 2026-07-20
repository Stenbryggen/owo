import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from src.owo.components.inventory import Inventory
from src.owo.components.position import Position
from src.owo.core.interaction import has_nearby_structure
from src.owo.core.resource_spawning import spawn_structure
from src.owo.core.validation import validate_recipe_dict


@dataclass
class Recipe:
    name: str
    inputs: Dict[str, float]
    output_item: str
    output_count: float
    time_hours: float
    output_type: str = "item"  # "item" (goes to inventory) | "structure" (placed in the world)
    requires_nearby: Optional[str] = None  # a Renderable.kind that must be nearby to craft this


def load_recipes(recipes_dir: str) -> Dict[str, Recipe]:
    recipes = {}
    for path in sorted(Path(recipes_dir).glob("*.json")):
        data = json.loads(path.read_text())
        validate_recipe_dict(data, path.name)
        recipes[data["name"]] = Recipe(
            name=data["name"],
            inputs=data["inputs"],
            output_item=data["output_item"],
            output_count=data.get("output_count", 1),
            time_hours=data.get("time_hours", 1.0),
            output_type=data.get("output_type", "item"),
            requires_nearby=data.get("requires_nearby"),
        )
    return recipes


def can_craft(inventory: Inventory, recipe: Recipe) -> bool:
    return all(inventory.items.get(item, 0) >= qty for item, qty in recipe.inputs.items())


def perform_craft(world, events, recipes: Dict[str, Recipe], actor_name: str, recipe_name: str) -> bool:
    """Crafting a known recipe with enough materials (and, for structures
    like a cart or boat, being near a requires_nearby prop such as a
    workbench) is instantaneous for now - time_hours is stored per recipe
    for a future progress-bar/queue, but doesn't gate anything yet.
    Returns whether the craft happened."""
    actor = world.get_entity_by_name(actor_name)
    recipe = recipes.get(recipe_name)
    if actor is None or recipe is None:
        return False

    inventory = actor.get_component(Inventory)
    if inventory is None or not can_craft(inventory, recipe):
        return False

    position = actor.get_component(Position)
    if recipe.requires_nearby:
        if position is None or not has_nearby_structure(world, position, recipe.requires_nearby):
            return False

    for item, qty in recipe.inputs.items():
        inventory.items[item] -= qty
        if inventory.items[item] <= 0:
            del inventory.items[item]

    if recipe.output_type == "structure":
        if position is not None:
            spawn_structure(world, position.x, position.y, recipe.output_item, name_prefix=recipe.output_item.title())
    else:
        inventory.items[recipe.output_item] = inventory.items.get(recipe.output_item, 0.0) + recipe.output_count

    events.publish(
        "item_crafted",
        {"entity": actor_name, "item": recipe.output_item, "count": recipe.output_count},
    )
    return True
