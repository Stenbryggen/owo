import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from src.owo.components.inventory import Inventory


@dataclass
class Recipe:
    name: str
    inputs: Dict[str, float]
    output_item: str
    output_count: float
    time_hours: float


def load_recipes(recipes_dir: str) -> Dict[str, Recipe]:
    recipes = {}
    for path in sorted(Path(recipes_dir).glob("*.json")):
        data = json.loads(path.read_text())
        recipes[data["name"]] = Recipe(
            name=data["name"],
            inputs=data["inputs"],
            output_item=data["output_item"],
            output_count=data.get("output_count", 1),
            time_hours=data.get("time_hours", 1.0),
        )
    return recipes


def can_craft(inventory: Inventory, recipe: Recipe) -> bool:
    return all(inventory.items.get(item, 0) >= qty for item, qty in recipe.inputs.items())


def perform_craft(world, events, recipes: Dict[str, Recipe], actor_name: str, recipe_name: str) -> bool:
    """Crafting a known recipe with enough materials is instantaneous for
    now - time_hours is stored per recipe for a future progress-bar/queue,
    but doesn't gate anything yet. Returns whether the craft happened."""
    actor = world.get_entity_by_name(actor_name)
    recipe = recipes.get(recipe_name)
    if actor is None or recipe is None:
        return False

    inventory = actor.get_component(Inventory)
    if inventory is None or not can_craft(inventory, recipe):
        return False

    for item, qty in recipe.inputs.items():
        inventory.items[item] -= qty
        if inventory.items[item] <= 0:
            del inventory.items[item]

    inventory.items[recipe.output_item] = inventory.items.get(recipe.output_item, 0.0) + recipe.output_count
    events.publish(
        "item_crafted",
        {"entity": actor_name, "item": recipe.output_item, "count": recipe.output_count},
    )
    return True
