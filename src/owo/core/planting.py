from src.owo.components.inventory import Inventory
from src.owo.components.position import Position
from src.owo.core.resource_spawning import spawn_tree

SEED_ITEM = "seed"


def perform_plant(world, events, actor_name: str) -> bool:
    actor = world.get_entity_by_name(actor_name)
    if actor is None:
        return False

    inventory = actor.get_component(Inventory)
    pos = actor.get_component(Position)
    if inventory is None or pos is None or inventory.items.get(SEED_ITEM, 0) < 1:
        return False

    inventory.items[SEED_ITEM] -= 1
    if inventory.items[SEED_ITEM] <= 0:
        del inventory.items[SEED_ITEM]

    tree = spawn_tree(world, pos.x, pos.y, mature=False)
    events.publish("tree_planted", {"entity": actor_name, "tree": tree.name})
    return True
