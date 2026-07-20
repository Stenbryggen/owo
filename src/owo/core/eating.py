from src.owo.components.energy import Energy
from src.owo.components.inventory import Inventory


def perform_eat(world, events, actor_name: str) -> bool:
    """Eats one unit of whichever known food (any ResourceType with
    food_energy set - see core/resource_types.py) the actor is carrying
    that restores the most energy. Returns whether anything was eaten."""
    actor = world.get_entity_by_name(actor_name)
    if actor is None:
        return False

    inventory = actor.get_component(Inventory)
    energy = actor.get_component(Energy)
    if inventory is None or energy is None:
        return False

    available = [
        (rtype.resource_type, rtype.food_energy)
        for rtype in world.resource_types.values()
        if rtype.food_energy and inventory.items.get(rtype.resource_type, 0) >= 1
    ]
    if not available:
        return False

    food, restore = max(available, key=lambda pair: pair[1])

    inventory.items[food] -= 1
    if inventory.items[food] <= 0:
        del inventory.items[food]

    energy.current = min(energy.max_energy, energy.current + restore)
    events.publish("food_eaten", {"entity": actor_name, "food": food, "energy_restored": restore})
    return True
