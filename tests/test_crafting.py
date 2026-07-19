from pathlib import Path

from src.owo.components.inventory import Inventory
from src.owo.core.crafting import can_craft, load_recipes, perform_craft
from src.owo.core.ecs import World
from src.owo.core.events import EventBus

REPO_ROOT = Path(__file__).resolve().parent.parent
RECIPES_DIR = REPO_ROOT / "content" / "recipes"


def test_load_recipes_finds_axe_and_pickaxe():
    recipes = load_recipes(str(RECIPES_DIR))
    assert "axe" in recipes
    assert "pickaxe" in recipes
    assert recipes["axe"].inputs == {"wood": 3, "stone": 1}


def test_can_craft_checks_material_sufficiency():
    inventory = Inventory(items={"wood": 3, "stone": 1})
    recipes = load_recipes(str(RECIPES_DIR))
    assert can_craft(inventory, recipes["axe"]) is True

    inventory.items["stone"] = 0
    assert can_craft(inventory, recipes["axe"]) is False


def test_perform_craft_consumes_inputs_and_produces_output():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Inventory(items={"wood": 3, "stone": 1}))
    recipes = load_recipes(str(RECIPES_DIR))

    assert perform_craft(world, events, recipes, "Actor", "axe") is True

    inventory = actor.get_component(Inventory)
    assert inventory.items.get("wood", 0) == 0  # fully consumed
    assert "stone" not in inventory.items  # fully consumed, removed rather than left at 0
    assert inventory.items["axe"] == 1


def test_perform_craft_fails_without_enough_materials():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Inventory(items={"wood": 1}))
    recipes = load_recipes(str(RECIPES_DIR))

    assert perform_craft(world, events, recipes, "Actor", "axe") is False
    assert "axe" not in actor.get_component(Inventory).items


def test_perform_craft_publishes_item_crafted_event():
    world = World()
    events = EventBus()
    fired = []
    events.subscribe("item_crafted", lambda p: fired.append(p))

    actor = world.create_entity("Actor")
    actor.add_component(Inventory(items={"wood": 2, "stone": 3}))
    recipes = load_recipes(str(RECIPES_DIR))

    perform_craft(world, events, recipes, "Actor", "pickaxe")

    assert fired == [{"entity": "Actor", "item": "pickaxe", "count": 1}]
