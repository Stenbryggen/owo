import math

from src.owo.components.harvestable import Harvestable
from src.owo.components.position import Position
from src.owo.components.quest import Quest
from src.owo.components.renderable import Renderable

INTERACT_RADIUS = 100
STRUCTURE_RADIUS = 150


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


def has_nearby_structure(world, player_pos, kind: str, radius: float = STRUCTURE_RADIUS) -> bool:
    """Whether a placed structure of the given Renderable.kind (e.g.
    "workbench") is within radius of player_pos - the gate for recipes
    with requires_nearby set."""
    if player_pos is None:
        return False

    for entity in world.entities.values():
        renderable = entity.get_component(Renderable)
        if renderable is None or renderable.kind != kind:
            continue
        pos = entity.get_component(Position)
        if pos is None:
            continue
        if math.hypot(pos.x - player_pos.x, pos.y - player_pos.y) <= radius:
            return True
    return False


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
