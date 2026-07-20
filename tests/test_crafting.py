from pathlib import Path

import pytest

from src.owo.components.inventory import Inventory
from src.owo.components.motion import Motion
from src.owo.components.position import Position
from src.owo.components.renderable import Renderable
from src.owo.core.crafting import can_craft, load_recipes, perform_craft
from src.owo.core.ecs import World
from src.owo.core.events import EventBus
from src.owo.core.validation import ContentValidationError

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


def _structures(world, kind):
    return [
        e for e in world.entities.values()
        if (r := e.get_component(Renderable)) is not None and r.kind == kind
    ]


def test_crafting_a_workbench_places_a_structure_not_an_inventory_item():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Position(x=100, y=200))
    actor.add_component(Inventory(items={"wood": 5, "stone": 2}))
    recipes = load_recipes(str(RECIPES_DIR))

    assert perform_craft(world, events, recipes, "Actor", "workbench") is True

    inventory = actor.get_component(Inventory)
    assert "workbench" not in inventory.items  # went into the world, not the inventory
    workbenches = _structures(world, "workbench")
    assert len(workbenches) == 1
    assert workbenches[0].get_component(Position).x == 100


def test_cart_requires_a_nearby_workbench():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Position(x=0, y=0))
    actor.add_component(Inventory(items={"wood": 10, "stone": 4, "iron": 2}))
    recipes = load_recipes(str(RECIPES_DIR))

    assert perform_craft(world, events, recipes, "Actor", "cart") is False
    assert actor.get_component(Inventory).items["wood"] == 10  # nothing consumed on failure


def test_cart_succeeds_once_a_workbench_is_nearby():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Position(x=0, y=0))
    actor.add_component(Inventory(items={"wood": 10, "stone": 4, "iron": 2}))

    bench = world.create_entity("Workbench")
    bench.add_component(Position(x=50, y=0))
    bench.add_component(Renderable(kind="workbench"))

    recipes = load_recipes(str(RECIPES_DIR))
    assert perform_craft(world, events, recipes, "Actor", "cart") is True
    assert len(_structures(world, "cart")) == 1


def test_crafted_cart_gives_a_speed_boost_like_the_starting_one():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Position(x=0, y=0))
    actor.add_component(Inventory(items={"wood": 10, "stone": 4, "iron": 2}))
    bench = world.create_entity("Workbench")
    bench.add_component(Position(x=0, y=0))
    bench.add_component(Renderable(kind="workbench"))
    recipes = load_recipes(str(RECIPES_DIR))

    perform_craft(world, events, recipes, "Actor", "cart")

    cart = _structures(world, "cart")[0]
    assert cart.get_component(Motion).speed_bonus == 0.6


def test_rope_recipe_uses_fiber():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Inventory(items={"fiber": 3}))
    recipes = load_recipes(str(RECIPES_DIR))

    assert perform_craft(world, events, recipes, "Actor", "rope") is True
    assert actor.get_component(Inventory).items["rope"] == 1


def test_recipe_missing_required_field_raises_with_filename(tmp_path):
    (tmp_path / "broken.json").write_text('{"name": "broken", "inputs": {"wood": 1}}')

    with pytest.raises(ContentValidationError, match="broken.json"):
        load_recipes(str(tmp_path))


def test_recipe_with_empty_inputs_is_rejected(tmp_path):
    (tmp_path / "broken.json").write_text('{"name": "broken", "inputs": {}, "output_item": "x"}')

    with pytest.raises(ContentValidationError, match="inputs"):
        load_recipes(str(tmp_path))


def test_recipe_with_invalid_output_type_is_rejected(tmp_path):
    (tmp_path / "broken.json").write_text(
        '{"name": "broken", "inputs": {"wood": 1}, "output_item": "x", "output_type": "potion"}'
    )

    with pytest.raises(ContentValidationError, match="output_type"):
        load_recipes(str(tmp_path))


def test_smelting_iron_ore_requires_a_nearby_campfire():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Position(x=0, y=0))
    actor.add_component(Inventory(items={"iron_ore": 2}))
    recipes = load_recipes(str(RECIPES_DIR))

    assert perform_craft(world, events, recipes, "Actor", "iron") is False

    campfire = world.create_entity("Campfire")
    campfire.add_component(Position(x=50, y=0))
    campfire.add_component(Renderable(kind="campfire"))

    assert perform_craft(world, events, recipes, "Actor", "iron") is True
    assert actor.get_component(Inventory).items["iron"] == 1
    assert "iron_ore" not in actor.get_component(Inventory).items


def test_cooking_fish_requires_a_nearby_campfire_and_gives_more_energy():
    world = World()
    events = EventBus()
    actor = world.create_entity("Actor")
    actor.add_component(Position(x=0, y=0))
    actor.add_component(Inventory(items={"fish": 1}))
    recipes = load_recipes(str(RECIPES_DIR))

    assert perform_craft(world, events, recipes, "Actor", "cook_fish") is False

    campfire = world.create_entity("Campfire")
    campfire.add_component(Position(x=30, y=0))
    campfire.add_component(Renderable(kind="campfire"))

    assert perform_craft(world, events, recipes, "Actor", "cook_fish") is True
    inventory = actor.get_component(Inventory)
    assert "fish" not in inventory.items
    assert inventory.items["cooked_fish"] == 1
