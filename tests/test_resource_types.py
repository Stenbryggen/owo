from pathlib import Path

import pytest

from src.owo.components.harvestable import Harvestable
from src.owo.components.inventory import Inventory
from src.owo.components.renderable import Renderable
from src.owo.core.ecs import World
from src.owo.core.resource_spawning import spawn_resource
from src.owo.core.resource_types import load_resource_types
from src.owo.core.validation import ContentValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_TYPES_DIR = REPO_ROOT / "content" / "resource_types"


def test_load_resource_types_finds_the_known_content_files():
    resource_types = load_resource_types(str(RESOURCE_TYPES_DIR))
    for name in ("tree", "mine", "ore_mine", "bush", "berry_bush", "fishing_spot", "nuts"):
        assert name in resource_types


def test_a_brand_new_resource_type_works_through_only_a_json_file(tmp_path):
    """The point of the whole registry: adding "copper_mine" here - a type
    that never existed in this codebase - needs zero new Python. Same
    generic spawn_resource() and Harvestable component every other
    resource type already goes through."""
    (tmp_path / "copper_mine.json").write_text("""
    {
      "name": "copper_mine",
      "renderable_kind": "copper_mine",
      "resource_type": "copper",
      "max_amount": 10.0,
      "regen_per_hour": 0.2,
      "required_tool": "pickaxe",
      "on_depleted": "regen",
      "depleted_kind": "empty_mine",
      "worldgen": {"enabled": true, "chance": 0.2}
    }
    """)

    resource_types = load_resource_types(str(tmp_path))
    copper_mine = resource_types["copper_mine"]

    world = World()
    entity = spawn_resource(world, 100.0, 200.0, copper_mine)

    harvestable = entity.get_component(Harvestable)
    assert harvestable.resource_type == "copper"
    assert harvestable.amount == 10.0
    assert harvestable.required_tool == "pickaxe"
    assert entity.get_component(Renderable).kind == "copper_mine"


def test_worldgen_picks_up_the_new_type_automatically(tmp_path):
    (tmp_path / "copper_mine.json").write_text("""
    {
      "name": "copper_mine",
      "renderable_kind": "copper_mine",
      "resource_type": "copper",
      "max_amount": 10.0,
      "worldgen": {"enabled": true, "chance": 1.0}
    }
    """)

    from src.owo.core.terrain import Terrain
    from src.owo.core.worldgen import _is_sea_chunk, generate_chunk

    world = World()
    world.terrain = Terrain()
    world.resource_types = load_resource_types(str(tmp_path))

    chunk_x = next(cx for cx in range(200) if not _is_sea_chunk(1, cx, 50))
    generate_chunk(world, chunk_x, 50, base_seed=1)

    kinds = {e.get_component(Renderable).kind for e in world.entities.values()}
    assert "copper_mine" in kinds


def test_missing_required_field_raises_with_filename(tmp_path):
    (tmp_path / "broken.json").write_text('{"name": "broken", "renderable_kind": "x"}')

    with pytest.raises(ContentValidationError, match="broken.json"):
        load_resource_types(str(tmp_path))


def test_invalid_on_depleted_value_is_rejected(tmp_path):
    (tmp_path / "broken.json").write_text("""
    {"name": "broken", "renderable_kind": "x", "resource_type": "x",
     "max_amount": 1.0, "on_depleted": "explode"}
    """)

    with pytest.raises(ContentValidationError, match="on_depleted"):
        load_resource_types(str(tmp_path))


def test_unknown_worldgen_field_is_rejected(tmp_path):
    (tmp_path / "broken.json").write_text("""
    {"name": "broken", "renderable_kind": "x", "resource_type": "x",
     "max_amount": 1.0, "worldgen": {"typo_field": true}}
    """)

    with pytest.raises(ContentValidationError, match="worldgen"):
        load_resource_types(str(tmp_path))


def test_ore_mine_yields_raw_iron_ore_not_finished_iron():
    resource_types = load_resource_types(str(RESOURCE_TYPES_DIR))
    assert resource_types["ore_mine"].resource_type == "iron_ore"
