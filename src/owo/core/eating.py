from src.owo.components.energy import Energy
from src.owo.components.inventory import Inventory

# Energy restored per unit eaten, roughly proportional to how much effort
# each food takes to get (berries are quick to gather, fish takes longest).
FOOD_ENERGY = {
    "berries": 8.0,
    "nuts": 12.0,
    "fish": 20.0,
}


def perform_eat(world, events, actor_name: str) -> bool:
    """Eats one unit of whichever known food the actor is carrying that
    restores the most energy. Returns whether anything was eaten."""
    actor = world.get_entity_by_name(actor_name)
    if actor is None:
        return False

    inventory = actor.get_component(Inventory)
    energy = actor.get_component(Energy)
    if inventory is None or energy is None:
        return False

    available = [
        (food, restore) for food, restore in FOOD_ENERGY.items()
        if inventory.items.get(food, 0) >= 1
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
