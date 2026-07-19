import math

from src.owo.components.motion import Motion
from src.owo.components.position import Position

BOOST_RADIUS = 120.0


def speed_multiplier(world, position: Position) -> float:
    """1.0 plus the speed_bonus of every Motion-carrying entity (cart,
    boots, ...) within BOOST_RADIUS of position - an aura effect, same
    pattern as ThermalComponent's effect on energy drain."""
    if position is None:
        return 1.0

    bonus = 0.0
    for entity in world.entities.values():
        motion = entity.get_component(Motion)
        if motion is None or motion.speed_bonus == 0.0:
            continue
        pos = entity.get_component(Position)
        if pos is None:
            continue
        if math.hypot(pos.x - position.x, pos.y - position.y) <= BOOST_RADIUS:
            bonus += motion.speed_bonus

    return 1.0 + bonus
