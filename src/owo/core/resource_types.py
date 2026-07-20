import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from src.owo.core.validation import validate_resource_type_dict


@dataclass
class GrowthSpec:
    enabled: bool = False
    sapling_kind: str = "sapling"
    mature_at_days: int = 3
    reproduction_chance: float = 0.0


@dataclass
class WorldgenSpec:
    """How core/worldgen.py scatters this resource type per chunk: either a
    random count in [count_min, count_max] (trees, bushes - several per
    chunk), or a chance of exactly one appearing (mines - rarer, singular).
    requires_lake is the one placement rule that isn't purely declarative
    (a fishing spot needs to know where the chunk's lake shore is)."""
    enabled: bool = False
    chance: float = 0.0
    count_min: int = 0
    count_max: int = 0
    requires_lake: bool = False


@dataclass
class ResourceType:
    name: str
    renderable_kind: str
    resource_type: str  # item name granted per unit harvested
    max_amount: float
    regen_per_hour: float = 0.0
    required_tool: str = ""
    on_depleted: str = "remove"  # "remove" | "regen"
    depleted_kind: str = ""
    food_energy: Optional[float] = None  # if set, eatable - see core/eating.py
    growth: GrowthSpec = field(default_factory=GrowthSpec)
    worldgen: WorldgenSpec = field(default_factory=WorldgenSpec)


def load_resource_types(resource_types_dir: str) -> Dict[str, ResourceType]:
    """Loads every content/resource_types/*.json file into a ResourceType.
    Adding a brand new harvestable (a copper vein, a mushroom patch, ...)
    is then just a new JSON file here - no new Python function, mirroring
    how content/recipes/*.json + load_recipes() already works for crafting."""
    resource_types = {}
    for path in sorted(Path(resource_types_dir).glob("*.json")):
        data = json.loads(path.read_text())
        validate_resource_type_dict(data, path.name)
        resource_types[data["name"]] = ResourceType(
            name=data["name"],
            renderable_kind=data["renderable_kind"],
            resource_type=data["resource_type"],
            max_amount=data["max_amount"],
            regen_per_hour=data.get("regen_per_hour", 0.0),
            required_tool=data.get("required_tool", ""),
            on_depleted=data.get("on_depleted", "remove"),
            depleted_kind=data.get("depleted_kind", ""),
            food_energy=data.get("food_energy"),
            growth=GrowthSpec(**data.get("growth", {})),
            worldgen=WorldgenSpec(**data.get("worldgen", {})),
        )
    return resource_types
