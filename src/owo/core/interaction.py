import math

from src.owo.components.harvestable import Harvestable
from src.owo.components.position import Position
from src.owo.components.quest import Quest

INTERACT_RADIUS = 100


def find_interactable_quest(world, player_pos):
    """Nearest open/in-progress quest entity within INTERACT_RADIUS of
    player_pos, or None. Shared by the frontend's interact prompt, the
    single-process app's "E to work" handling, and the multiplayer
    server's authoritative work resolution, so all three agree on what's
    reachable."""
    if player_pos is None:
        return None

    best, best_dist = None, INTERACT_RADIUS
    for entity in world.entities.values():
        quest = entity.get_component(Quest)
        if quest is None or quest.status == "completed":
            continue
        pos = entity.get_component(Position)
        if pos is None:
            continue
        dist = math.hypot(pos.x - player_pos.x, pos.y - player_pos.y)
        if dist <= best_dist:
            best, best_dist = entity, dist
    return best


def find_interactable_resource(world, player_pos):
    """Nearest harvestable resource node (tree, mine, ...) within
    INTERACT_RADIUS that still has something to give, or None."""
    if player_pos is None:
        return None

    best, best_dist = None, INTERACT_RADIUS
    for entity in world.entities.values():
        harvestable = entity.get_component(Harvestable)
        if harvestable is None or harvestable.amount <= 0:
            continue
        pos = entity.get_component(Position)
        if pos is None:
            continue
        dist = math.hypot(pos.x - player_pos.x, pos.y - player_pos.y)
        if dist <= best_dist:
            best, best_dist = entity, dist
    return best
