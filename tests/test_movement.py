from src.owo.components.motion import Motion
from src.owo.components.position import Position
from src.owo.core.ecs import World
from src.owo.core.movement import speed_multiplier


def test_no_nearby_motion_entities_gives_base_speed():
    world = World()
    player = world.create_entity("Player1")
    player.add_component(Position(x=0, y=0))

    assert speed_multiplier(world, player.get_component(Position)) == 1.0


def test_nearby_cart_boosts_speed():
    world = World()
    player = world.create_entity("Player1")
    player.add_component(Position(x=0, y=0))

    cart = world.create_entity("Cart")
    cart.add_component(Position(x=10, y=0))
    cart.add_component(Motion(speed_bonus=0.6))

    assert speed_multiplier(world, player.get_component(Position)) == 1.6


def test_far_away_cart_has_no_effect():
    world = World()
    player = world.create_entity("Player1")
    player.add_component(Position(x=0, y=0))

    cart = world.create_entity("Cart")
    cart.add_component(Position(x=9999, y=9999))
    cart.add_component(Motion(speed_bonus=0.6))

    assert speed_multiplier(world, player.get_component(Position)) == 1.0
