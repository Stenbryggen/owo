import hashlib
import random
from typing import Tuple

from src.owo.core.resource_spawning import (
    spawn_berry_bush,
    spawn_bush,
    spawn_fishing_spot,
    spawn_mine,
    spawn_ore_mine,
    spawn_tree,
)
from src.owo.core.terrain import TILE_SIZE, carve_lake_with_island, world_to_tile

CHUNK_SIZE = 16  # tiles per chunk side

LAKE_CHANCE = 0.25
FISHING_SPOT_CHANCE = 0.5  # conditional on this chunk having a lake
TREE_COUNT_RANGE = (2, 6)
MINE_CHANCE = 0.5
ORE_MINE_CHANCE = 0.15
BUSH_COUNT_RANGE = (0, 3)
BERRY_BUSH_COUNT_RANGE = (0, 2)

# Sea: a much bigger, contiguous body of water spanning a whole region of
# chunks, distinct from the small in-chunk lakes above. Regions are a
# coarser grid layered on top of chunks - same determinism/seeding idea.
SEA_REGION_CHUNKS = 4
SEA_CHANCE = 0.15


def chunk_of(col: int, row: int, chunk_size: int = CHUNK_SIZE) -> Tuple[int, int]:
    return col // chunk_size, row // chunk_size


def _region_seed(base_seed: int, region_x: int, region_y: int) -> int:
    digest = hashlib.sha256(f"{base_seed}:sea:{region_x}:{region_y}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _is_sea_chunk(base_seed: int, chunk_x: int, chunk_y: int, region_chunks: int = SEA_REGION_CHUNKS) -> bool:
    region_x, region_y = chunk_x // region_chunks, chunk_y // region_chunks
    rng = random.Random(_region_seed(base_seed, region_x, region_y))
    return rng.random() < SEA_CHANCE


def _chunk_seed(base_seed: int, chunk_x: int, chunk_y: int) -> int:
    """Deterministic per-chunk seed: the same chunk always generates the
    same content, independent of generation order or which player
    triggered it - two players approaching the same unexplored area from
    different directions still see the same world."""
    digest = hashlib.sha256(f"{base_seed}:{chunk_x}:{chunk_y}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def generate_chunk(world, chunk_x: int, chunk_y: int, base_seed: int = 0, chunk_size: int = CHUNK_SIZE) -> None:
    """Fills terrain and scatters resource entities for one chunk. Callers
    should check world.loaded_chunks first - calling this twice for the
    same chunk would scatter resources twice."""
    origin_col = chunk_x * chunk_size
    origin_row = chunk_y * chunk_size

    if _is_sea_chunk(base_seed, chunk_x, chunk_y, SEA_REGION_CHUNKS):
        for col in range(origin_col, origin_col + chunk_size):
            for row in range(origin_row, origin_row + chunk_size):
                world.terrain.set(col, row, "water")
        return  # open sea - nothing grows or gets mined here

    rng = random.Random(_chunk_seed(base_seed, chunk_x, chunk_y))

    if rng.random() < LAKE_CHANCE:
        lake_col = origin_col + rng.randint(3, chunk_size - 4)
        lake_row = origin_row + rng.randint(3, chunk_size - 4)
        lake_radius = rng.randint(2, 3)
        carve_lake_with_island(world.terrain, lake_col, lake_row, lake_radius, 1)

        if rng.random() < FISHING_SPOT_CHANCE:
            shore_col = lake_col + lake_radius + 1
            shore_row = lake_row
            if world.terrain.get(shore_col, shore_row) == world.terrain.default:
                spawn_fishing_spot(
                    world, shore_col * TILE_SIZE + TILE_SIZE // 2, shore_row * TILE_SIZE + TILE_SIZE // 2
                )

    for _ in range(rng.randint(*TREE_COUNT_RANGE)):
        col = origin_col + rng.randint(0, chunk_size - 1)
        row = origin_row + rng.randint(0, chunk_size - 1)
        if world.terrain.get(col, row) != world.terrain.default:
            continue
        spawn_tree(world, col * TILE_SIZE + TILE_SIZE // 2, row * TILE_SIZE + TILE_SIZE // 2, mature=True)

    if rng.random() < MINE_CHANCE:
        col = origin_col + rng.randint(0, chunk_size - 1)
        row = origin_row + rng.randint(0, chunk_size - 1)
        if world.terrain.get(col, row) == world.terrain.default:
            spawn_mine(world, col * TILE_SIZE + TILE_SIZE // 2, row * TILE_SIZE + TILE_SIZE // 2)

    if rng.random() < ORE_MINE_CHANCE:
        col = origin_col + rng.randint(0, chunk_size - 1)
        row = origin_row + rng.randint(0, chunk_size - 1)
        if world.terrain.get(col, row) == world.terrain.default:
            spawn_ore_mine(world, col * TILE_SIZE + TILE_SIZE // 2, row * TILE_SIZE + TILE_SIZE // 2)

    for _ in range(rng.randint(*BUSH_COUNT_RANGE)):
        col = origin_col + rng.randint(0, chunk_size - 1)
        row = origin_row + rng.randint(0, chunk_size - 1)
        if world.terrain.get(col, row) != world.terrain.default:
            continue
        spawn_bush(world, col * TILE_SIZE + TILE_SIZE // 2, row * TILE_SIZE + TILE_SIZE // 2)

    for _ in range(rng.randint(*BERRY_BUSH_COUNT_RANGE)):
        col = origin_col + rng.randint(0, chunk_size - 1)
        row = origin_row + rng.randint(0, chunk_size - 1)
        if world.terrain.get(col, row) != world.terrain.default:
            continue
        spawn_berry_bush(world, col * TILE_SIZE + TILE_SIZE // 2, row * TILE_SIZE + TILE_SIZE // 2)


def ensure_chunks_loaded(
    world, player_x: float, player_y: float,
    radius_chunks: int = 2, base_seed: int = 0, chunk_size: int = CHUNK_SIZE,
) -> None:
    """Generates every not-yet-loaded chunk within radius_chunks of the
    player. Cheap to call every tick for every player - already-loaded
    chunks are a single set lookup."""
    center_col, center_row = world_to_tile(player_x, player_y)
    center_chunk = chunk_of(center_col, center_row, chunk_size)

    for dx in range(-radius_chunks, radius_chunks + 1):
        for dy in range(-radius_chunks, radius_chunks + 1):
            chunk = (center_chunk[0] + dx, center_chunk[1] + dy)
            if chunk in world.loaded_chunks:
                continue
            generate_chunk(world, chunk[0], chunk[1], base_seed, chunk_size)
            world.loaded_chunks.add(chunk)
