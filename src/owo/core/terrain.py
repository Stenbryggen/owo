import math
from typing import Dict, Tuple

TILE_SIZE = 80
DEFAULT_TILE = "grass"


class Terrain:
    """A sparse tile grid: only tiles that differ from `default` are stored,
    so most of the map costs nothing. This is the doc's "world remembers
    permanent geometric changes" - a filled-in lake tile stays filled until
    someone changes it back, including across save/load."""

    def __init__(self, width_tiles: int, height_tiles: int, default: str = DEFAULT_TILE):
        self.width = width_tiles
        self.height = height_tiles
        self.default = default
        self.tiles: Dict[Tuple[int, int], str] = {}

    def get(self, col: int, row: int) -> str:
        return self.tiles.get((col, row), self.default)

    def set(self, col: int, row: int, tile_type: str) -> None:
        if tile_type == self.default:
            self.tiles.pop((col, row), None)
        else:
            self.tiles[(col, row)] = tile_type


def world_to_tile(x: float, y: float, tile_size: int = TILE_SIZE) -> Tuple[int, int]:
    return int(x // tile_size), int(y // tile_size)


def carve_lake_with_island(
    terrain: Terrain, center_col: int, center_row: int,
    radius_tiles: int, island_radius_tiles: int,
) -> None:
    """Sets up the starting lake-with-an-island feature from the doc's
    example of a permanent geometric change. The island itself is left at
    the default tile (grass) - only the water ring is carved."""
    for col in range(center_col - radius_tiles, center_col + radius_tiles + 1):
        for row in range(center_row - radius_tiles, center_row + radius_tiles + 1):
            dist = math.hypot(col - center_col, row - center_row)
            if dist <= island_radius_tiles:
                continue
            if dist <= radius_tiles:
                terrain.set(col, row, "water")
