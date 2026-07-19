from src.owo.components import harvestable, position, renderable  # noqa: F401 - registers components
from src.owo.core.ecs import World
from src.owo.core.terrain import Terrain
from src.owo.core.worldgen import SEA_REGION_CHUNKS, _is_sea_chunk, chunk_of, ensure_chunks_loaded, generate_chunk


def _make_world():
    world = World()
    world.terrain = Terrain()
    return world


def test_chunk_of_maps_tile_coords_to_chunk_coords():
    assert chunk_of(0, 0, chunk_size=16) == (0, 0)
    assert chunk_of(15, 15, chunk_size=16) == (0, 0)
    assert chunk_of(16, 0, chunk_size=16) == (1, 0)
    assert chunk_of(-1, 0, chunk_size=16) == (-1, 0)


def test_generate_chunk_is_deterministic_for_the_same_seed():
    world_a = _make_world()
    generate_chunk(world_a, 5, -3, base_seed=42)

    world_b = _make_world()
    generate_chunk(world_b, 5, -3, base_seed=42)

    names_a = sorted(e.name.split("_")[0] for e in world_a.entities.values())
    names_b = sorted(e.name.split("_")[0] for e in world_b.entities.values())
    assert names_a == names_b
    assert dict(world_a.terrain.tiles) == dict(world_b.terrain.tiles)


def test_generate_chunk_differs_for_different_seeds_or_coords():
    world_a = _make_world()
    generate_chunk(world_a, 0, 0, base_seed=1)

    world_b = _make_world()
    generate_chunk(world_b, 0, 0, base_seed=2)

    # Not a strict guarantee for every possible pair, but true for these
    # picked seeds - documents that the seed actually matters.
    a = sorted((e.get_component(position.Position).x, e.get_component(position.Position).y)
               for e in world_a.entities.values())
    b = sorted((e.get_component(position.Position).x, e.get_component(position.Position).y)
               for e in world_b.entities.values())
    assert a != b


def test_ensure_chunks_loaded_marks_chunks_and_does_not_duplicate():
    world = _make_world()
    ensure_chunks_loaded(world, player_x=0, player_y=0, radius_chunks=1, base_seed=7)

    assert (0, 0) in world.loaded_chunks
    entity_count_after_first = len(world.entities)

    # Calling again for the same area must not scatter resources twice.
    ensure_chunks_loaded(world, player_x=0, player_y=0, radius_chunks=1, base_seed=7)
    assert len(world.entities) == entity_count_after_first


def test_ensure_chunks_loaded_expands_as_player_moves_far_away():
    world = _make_world()
    ensure_chunks_loaded(world, player_x=0, player_y=0, radius_chunks=1, base_seed=7)
    loaded_near_origin = set(world.loaded_chunks)

    ensure_chunks_loaded(world, player_x=100_000, player_y=100_000, radius_chunks=1, base_seed=7)

    assert world.loaded_chunks - loaded_near_origin  # new chunks were generated far away


def test_sea_chunk_is_entirely_water_and_has_no_resources():
    seed = None
    for candidate in range(200):
        cx = candidate * SEA_REGION_CHUNKS
        if _is_sea_chunk(1, cx, 0):
            seed, chunk_x = 1, cx
            break
    assert seed is not None, "expected at least one sea chunk within the search range"

    world = _make_world()
    generate_chunk(world, chunk_x, 0, base_seed=1)

    assert world.entities == {}
    assert all(t == "water" for t in world.terrain.tiles.values())


def test_sea_chunks_are_deterministic_for_the_same_seed():
    assert _is_sea_chunk(99, 40, 40) == _is_sea_chunk(99, 40, 40)


def test_whole_sea_region_shares_the_same_sea_status():
    # Every chunk in the same SEA_REGION_CHUNKS x SEA_REGION_CHUNKS block
    # must agree - a sea can't have holes at chunk region boundaries.
    base_x, base_y = 3 * SEA_REGION_CHUNKS, 5 * SEA_REGION_CHUNKS
    statuses = {
        _is_sea_chunk(7, base_x + dx, base_y + dy)
        for dx in range(SEA_REGION_CHUNKS)
        for dy in range(SEA_REGION_CHUNKS)
    }
    assert len(statuses) == 1
