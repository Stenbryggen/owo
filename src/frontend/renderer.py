import pygame

from src.owo.components.energy import Energy
from src.owo.components.harvestable import Harvestable
from src.owo.components.health import Health
from src.owo.components.inventory import Inventory
from src.owo.components.position import Position
from src.owo.components.quest import Quest
from src.owo.components.renderable import Renderable
from src.owo.components.skills import Skills
from src.owo.components.sleep import Sleep
from src.owo.components.thermal import Thermal
from src.owo.components.wallet import Wallet
from src.owo.core.interaction import find_interactable_quest, find_interactable_resource
from src.owo.core.terrain import TILE_SIZE, world_to_tile
from src.owo.core.work import quest_progress
from src.owo.core.worldgen import CHUNK_SIZE, chunk_of

DEFAULT_SCREEN_SIZE = (1600, 900)  # just the initial window size - it's resizable, see play.py

ENTITY_RADIUS = 34
BAR_WIDTH = 90
BAR_HEIGHT = 14

QUEST_STATUS_COLOR = {
    "open": (230, 195, 60),
    "in_progress": (80, 140, 220),
    "completed": (90, 200, 90),
}

DAY_BG = (135, 196, 235)
NIGHT_BG = (18, 24, 48)
SEASON_TINT = {
    "Winter": (210, 225, 245),
    "Summer": (255, 244, 200),
    "Spring": (215, 245, 210),
    "Autumn": (245, 220, 180),
}

GROUND_COLOR = (74, 130, 62)
TILE_COLORS = {
    "water": (58, 122, 190),
    "dirt": (122, 92, 56),
}


def is_night(world, config) -> bool:
    seasonal = config["world"]["seasonal_factors"][world.current_season]
    return world.current_time < seasonal["night_length_hours"]


def _blend(base, tint, amount=0.15):
    return tuple(int(base[i] + (tint[i] - base[i]) * amount) for i in range(3))


def ground_tint(world, config):
    if is_night(world, config):
        return _blend(GROUND_COLOR, (10, 10, 30), amount=0.5)
    return _blend(GROUND_COLOR, SEASON_TINT.get(world.current_season, GROUND_COLOR), amount=0.2)


def sky_color(world, config):
    base = NIGHT_BG if is_night(world, config) else DAY_BG
    tint = SEASON_TINT.get(world.current_season, base)
    return _blend(base, tint)


def _draw_terrain(surface, world, config, camera):
    terrain = world.terrain
    grass_color = ground_tint(world, config)
    night = is_night(world, config)

    if terrain is None:
        surface.fill(grass_color)
        return

    tile_colors = {"grass": grass_color}
    for tile_type, color in TILE_COLORS.items():
        tile_colors[tile_type] = _blend(color, (10, 10, 30), amount=0.35) if night else color

    # World is infinite, so the visible tile range is purely a function of
    # the camera/screen - there is no map edge to clamp to. Uses the actual
    # surface size (not a fixed constant) so a resized window just works.
    width, height = surface.get_size()
    col_start = int(camera[0] // TILE_SIZE)
    col_end = int((camera[0] + width) // TILE_SIZE) + 1
    row_start = int(camera[1] // TILE_SIZE)
    row_end = int((camera[1] + height) // TILE_SIZE) + 1

    for col in range(col_start, col_end):
        for row in range(row_start, row_end):
            tile_type = terrain.get(col, row)
            color = tile_colors.get(tile_type, (150, 150, 150))
            rect = (col * TILE_SIZE - camera[0], row * TILE_SIZE - camera[1], TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, color, rect)


def compute_camera(player_pos, screen_size):
    return player_pos.x - screen_size[0] / 2, player_pos.y - screen_size[1] / 2


def _bar(surface, x, y, ratio, color):
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(surface, (40, 40, 40), (x, y, BAR_WIDTH, BAR_HEIGHT), border_radius=2)
    pygame.draw.rect(surface, color, (x, y, int(BAR_WIDTH * ratio), BAR_HEIGHT), border_radius=2)


def _draw_living_entity(surface, font, x, y, entity):
    energy = entity.get_component(Energy)
    health = entity.get_component(Health)
    sleep = entity.get_component(Sleep)

    color = (90, 140, 220)
    if health and health.is_sick:
        color = (150, 90, 190)
    if sleep and sleep.is_sleeping:
        color = (70, 90, 150)

    pygame.draw.circle(surface, color, (x, y), ENTITY_RADIUS)
    pygame.draw.circle(surface, (20, 20, 20), (x, y), ENTITY_RADIUS, width=2)

    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - ENTITY_RADIUS - 26)))

    bar_x = x - BAR_WIDTH // 2
    if energy:
        _bar(surface, bar_x, y + ENTITY_RADIUS + 12,
             energy.current / energy.max_energy, (90, 200, 90))
    if health:
        _bar(surface, bar_x, y + ENTITY_RADIUS + 30,
             health.current / health.max_health, (210, 70, 70))

    if sleep and sleep.is_sleeping:
        zzz = font.render("Zzz", True, (230, 230, 255))
        surface.blit(zzz, (x + ENTITY_RADIUS - 8, y - ENTITY_RADIUS - 60))


def _draw_thermal_entity(surface, font, x, y, entity):
    flicker = 6 if (pygame.time.get_ticks() // 200) % 2 == 0 else 0
    pygame.draw.polygon(
        surface,
        (240, 120, 30),
        [(x, y - 30 - flicker), (x - 20, y + 16), (x + 20, y + 16)],
    )
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 60)))


def _draw_tree(surface, font, x, y, entity):
    pygame.draw.rect(surface, (110, 74, 40), (x - 6, y - 4, 12, 26))
    pygame.draw.circle(surface, (46, 110, 46), (x, y - 30), 32)
    pygame.draw.circle(surface, (30, 80, 30), (x, y - 30), 32, width=2)


def _draw_rock(surface, font, x, y, entity):
    pygame.draw.ellipse(surface, (130, 130, 135), (x - 26, y - 16, 52, 32))
    pygame.draw.ellipse(surface, (90, 90, 95), (x - 26, y - 16, 52, 32), width=2)


def _draw_sapling(surface, font, x, y, entity):
    pygame.draw.rect(surface, (110, 74, 40), (x - 3, y - 2, 6, 14))
    pygame.draw.circle(surface, (70, 150, 70), (x, y - 16), 14)
    pygame.draw.circle(surface, (40, 110, 40), (x, y - 16), 14, width=2)


def _draw_mine(surface, font, x, y, entity):
    pygame.draw.polygon(
        surface, (110, 100, 90),
        [(x - 34, y + 16), (x - 18, y - 24), (x + 4, y - 10), (x + 18, y - 28), (x + 34, y + 16)],
    )
    pygame.draw.polygon(
        surface, (60, 50, 45),
        [(x - 34, y + 16), (x - 18, y - 24), (x + 4, y - 10), (x + 18, y - 28), (x + 34, y + 16)],
        width=2,
    )
    pygame.draw.rect(surface, (20, 20, 20), (x - 10, y - 4, 20, 20))
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 42)))


def _draw_empty_mine(surface, font, x, y, entity):
    pygame.draw.ellipse(surface, (70, 60, 55), (x - 24, y - 8, 48, 20))
    pygame.draw.ellipse(surface, (30, 25, 22), (x - 24, y - 8, 48, 20), width=2)
    label = font.render(f"{entity.name} (empty)", True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 28)))


def _draw_quest_board(surface, font, x, y, entity):
    pygame.draw.rect(surface, (140, 100, 60), (x - 4, y - 4, 8, 34))
    pygame.draw.rect(surface, (170, 130, 85), (x - 26, y - 44, 52, 40))
    pygame.draw.rect(surface, (90, 60, 30), (x - 26, y - 44, 52, 40), width=2)
    mark = font.render("!", True, (200, 40, 40))
    surface.blit(mark, mark.get_rect(center=(x, y - 24)))
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 70)))


def _draw_chest(surface, font, x, y, entity):
    pygame.draw.rect(surface, (150, 105, 40), (x - 26, y - 16, 52, 30))
    pygame.draw.rect(surface, (90, 60, 20), (x - 26, y - 16, 52, 30), width=2)
    pygame.draw.rect(surface, (210, 180, 60), (x - 5, y - 16, 10, 12))
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 34)))


def _draw_cart(surface, font, x, y, entity):
    pygame.draw.rect(surface, (120, 80, 45), (x - 28, y - 14, 56, 24))
    pygame.draw.rect(surface, (70, 45, 25), (x - 28, y - 14, 56, 24), width=2)
    pygame.draw.circle(surface, (30, 30, 30), (x - 16, y + 14), 10)
    pygame.draw.circle(surface, (30, 30, 30), (x + 16, y + 14), 10)
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 28)))


def _draw_ore_mine(surface, font, x, y, entity):
    pygame.draw.polygon(
        surface, (150, 95, 70),
        [(x - 34, y + 16), (x - 18, y - 24), (x + 4, y - 10), (x + 18, y - 28), (x + 34, y + 16)],
    )
    pygame.draw.polygon(
        surface, (90, 55, 40),
        [(x - 34, y + 16), (x - 18, y - 24), (x + 4, y - 10), (x + 18, y - 28), (x + 34, y + 16)],
        width=2,
    )
    pygame.draw.rect(surface, (200, 120, 40), (x - 10, y - 4, 20, 20))
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 42)))


def _draw_bush(surface, font, x, y, entity):
    pygame.draw.circle(surface, (60, 130, 50), (x - 10, y - 6), 14)
    pygame.draw.circle(surface, (70, 145, 55), (x + 10, y - 6), 16)
    pygame.draw.circle(surface, (40, 100, 35), (x, y - 4), 18, width=2)


def _draw_empty_bush(surface, font, x, y, entity):
    pygame.draw.circle(surface, (110, 100, 70), (x, y - 4), 12, width=2)


def _draw_berry_bush(surface, font, x, y, entity):
    pygame.draw.circle(surface, (60, 130, 50), (x - 10, y - 6), 14)
    pygame.draw.circle(surface, (70, 145, 55), (x + 10, y - 6), 16)
    pygame.draw.circle(surface, (40, 100, 35), (x, y - 4), 18, width=2)
    for dx, dy in ((-8, -8), (6, -10), (0, 2), (10, -2)):
        pygame.draw.circle(surface, (190, 40, 60), (x + dx, y + dy), 3)


def _draw_fishing_spot(surface, font, x, y, entity):
    pygame.draw.ellipse(surface, (70, 140, 200), (x - 30, y - 12, 60, 24))
    pygame.draw.ellipse(surface, (40, 100, 160), (x - 30, y - 12, 60, 24), width=2)
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 24)))


def _draw_workbench(surface, font, x, y, entity):
    pygame.draw.rect(surface, (150, 110, 65), (x - 28, y - 10, 56, 20))
    pygame.draw.rect(surface, (90, 65, 35), (x - 28, y - 10, 56, 20), width=2)
    pygame.draw.rect(surface, (60, 45, 25), (x - 24, y + 10, 6, 16))
    pygame.draw.rect(surface, (60, 45, 25), (x + 18, y + 10, 6, 16))
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 26)))


def _draw_tent(surface, font, x, y, entity):
    pygame.draw.polygon(surface, (190, 170, 120), [(x, y - 34), (x - 30, y + 14), (x + 30, y + 14)])
    pygame.draw.polygon(surface, (130, 110, 70), [(x, y - 34), (x - 30, y + 14), (x + 30, y + 14)], width=2)
    pygame.draw.polygon(surface, (110, 90, 55), [(x, y - 34), (x - 8, y + 14), (x + 8, y + 14)])
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 46)))


def _draw_boat(surface, font, x, y, entity):
    pygame.draw.polygon(
        surface, (140, 95, 55),
        [(x - 36, y), (x - 24, y + 18), (x + 24, y + 18), (x + 36, y), (x - 36, y)],
    )
    pygame.draw.rect(surface, (90, 60, 30), (x - 2, y - 30, 4, 30))
    pygame.draw.polygon(surface, (230, 230, 220), [(x + 2, y - 28), (x + 2, y - 4), (x + 22, y - 4)])
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 40)))


def _draw_house(surface, font, x, y, entity):
    pygame.draw.rect(surface, (200, 190, 160), (x - 34, y - 10, 68, 40))
    pygame.draw.rect(surface, (110, 80, 50), (x - 34, y - 10, 68, 40), width=2)
    pygame.draw.polygon(surface, (150, 60, 50), [(x - 40, y - 10), (x, y - 44), (x + 40, y - 10)])
    pygame.draw.rect(surface, (90, 60, 35), (x - 8, y + 8, 16, 22))
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 56)))


def _draw_generic_prop(surface, font, x, y, entity):
    pygame.draw.rect(surface, (150, 150, 150), (x - 20, y - 20, 40, 40))
    label = font.render(entity.name, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 34)))


def _draw_quest_marker(surface, font, x, y, entity):
    quest = entity.get_component(Quest)
    color = QUEST_STATUS_COLOR.get(quest.status if quest else "open", (200, 200, 200))

    pygame.draw.rect(surface, (140, 100, 60), (x - 4, y - 4, 8, 40))
    banner = (x - 34, y - 46, 68, 32)
    pygame.draw.rect(surface, color, banner)
    pygame.draw.rect(surface, (40, 40, 40), banner, width=2)
    mark = font.render("$" if quest and quest.reward_gold else "XP", True, (30, 30, 30))
    surface.blit(mark, mark.get_rect(center=(x, y - 30)))

    title = quest.title if quest else entity.name
    label = font.render(title, True, (15, 15, 15))
    surface.blit(label, label.get_rect(center=(x, y - 78)))

    if quest:
        ratio = quest_progress(quest) / quest.effort_required if quest.effort_required else 1.0
        _bar(surface, x - BAR_WIDTH // 2, y + 8, ratio, color)


_PROP_DRAWERS = {
    "tree": _draw_tree,
    "sapling": _draw_sapling,
    "rock": _draw_rock,
    "mine": _draw_mine,
    "empty_mine": _draw_empty_mine,
    "ore_mine": _draw_ore_mine,
    "bush": _draw_bush,
    "empty_bush": _draw_empty_bush,
    "berry_bush": _draw_berry_bush,
    "fishing_spot": _draw_fishing_spot,
    "quest_board": _draw_quest_board,
    "chest": _draw_chest,
    "quest_marker": _draw_quest_marker,
    "cart": _draw_cart,
    "workbench": _draw_workbench,
    "tent": _draw_tent,
    "boat": _draw_boat,
    "house": _draw_house,
}


def _draw_harvestable_bar(surface, x, y, entity):
    harvestable = entity.get_component(Harvestable)
    if harvestable is None or harvestable.amount >= harvestable.max_amount:
        return
    ratio = harvestable.amount / harvestable.max_amount if harvestable.max_amount else 0.0
    _bar(surface, x - BAR_WIDTH // 2, y + 30, ratio, (150, 110, 60))


def _format_time(hours: float) -> str:
    h = int(hours) % 24
    m = int((hours - int(hours)) * 60)
    return f"{h:02d}:{m:02d}"


DEFAULT_CONTROLS_HINT = [
    "WASD/arrows = move",
    "E = work quest",
    "F = fill water",
    "F5 = save    F9 = load",
    "H = toggle this help",
    "ESC = quit",
]


def _draw_text_lines(surface, hud_font, lines, x0=16, y0=12):
    for i, text in enumerate(lines):
        label = hud_font.render(text, True, (15, 15, 15))
        bg = pygame.Surface(label.get_size())
        bg.set_alpha(140)
        bg.fill((255, 255, 255))
        surface.blit(bg, (x0, y0 + i * 38))
        surface.blit(label, (x0 + 4, y0 + 2 + i * 38))


def _draw_status_bar(surface, hud_font, world, config, paused: bool, time_scale: float):
    """Season/day/time - always visible, not part of the toggleable help."""
    night_label = "Night" if is_night(world, config) else "Day"
    lines = [
        f"Season: {world.current_season}  (Day {world.day_count})  {night_label}",
        f"Time: {_format_time(world.current_time)}    Speed: {time_scale:g}x"
        + ("  [PAUSED]" if paused else ""),
    ]
    _draw_text_lines(surface, hud_font, lines)


def _draw_player_panel(surface, font, world, player_name):
    """Gold + skills - small, always-visible corner panel. Inventory moved
    out into its own centered, I-toggled panel (_draw_inventory_panel)."""
    player = world.get_entity_by_name(player_name)
    if player is None:
        return

    wallet = player.get_component(Wallet)
    skills = player.get_component(Skills)

    lines = [f"Gold: {wallet.gold:.0f}" if wallet else "Gold: -"]
    if skills and skills.levels:
        for skill_name, level in sorted(skills.levels.items()):
            xp_in_level = skills.xp.get(skill_name, 0.0) % 100.0
            lines.append(f"{skill_name.title()} Lv{level}  ({xp_in_level:.0f}/100 xp)")
    else:
        lines.append("No skills yet")

    panel_width = 300
    panel_height = 16 + len(lines) * 32
    x0 = surface.get_width() - panel_width - 16
    y0 = 16

    panel = pygame.Surface((panel_width, panel_height))
    panel.set_alpha(160)
    panel.fill((255, 255, 255))
    surface.blit(panel, (x0, y0))

    for i, text in enumerate(lines):
        label = font.render(text, True, (15, 15, 15))
        surface.blit(label, (x0 + 14, y0 + 10 + i * 32))


def _centered_panel(surface, width_ratio=0.6, height_ratio=0.7):
    """Shared background for full-screen-ish overlays (map, inventory,
    help, build menu) - each toggled independently, drawn in the same
    style so they read as one family of "open a panel" screens."""
    width, height = surface.get_size()
    panel_w, panel_h = int(width * width_ratio), int(height * height_ratio)
    x0, y0 = (width - panel_w) // 2, (height - panel_h) // 2

    panel = pygame.Surface((panel_w, panel_h))
    panel.set_alpha(235)
    panel.fill((20, 20, 20))
    surface.blit(panel, (x0, y0))
    return x0, y0, panel_w, panel_h


def _draw_titled_panel(surface, hud_font, title, lines, width_ratio=0.6, height_ratio=0.7):
    x0, y0, panel_w, panel_h = _centered_panel(surface, width_ratio, height_ratio)

    title_label = hud_font.render(title, True, (255, 255, 255))
    surface.blit(title_label, (x0 + 16, y0 + 14))

    for i, text in enumerate(lines):
        label = hud_font.render(text, True, (230, 230, 230))
        surface.blit(label, (x0 + 20, y0 + 60 + i * 32))

    return x0, y0, panel_w, panel_h


def _draw_controls_help(surface, hud_font, controls_hint):
    """The toggleable (H key) help overview - one control per line,
    centered like the map/inventory/build-menu panels."""
    lines = [controls_hint] if isinstance(controls_hint, str) else list(controls_hint)
    _draw_titled_panel(surface, hud_font, "Help (H to close)", lines, height_ratio=0.6)


def _draw_inventory_panel(surface, hud_font, world, player_name):
    """The toggleable (I key) inventory overview - one item per line."""
    player = world.get_entity_by_name(player_name)
    inventory = player.get_component(Inventory) if player else None

    if inventory and inventory.items:
        lines = [f"{name} x{int(count)}" for name, count in sorted(inventory.items.items())]
    else:
        lines = ["(empty)"]

    _draw_titled_panel(surface, hud_font, "Inventory (I to close)", lines)


def _draw_interact_hint(surface, hud_font, quest_entity):
    if quest_entity is None:
        return
    quest = quest_entity.get_component(Quest)
    text = f"Press E to work: {quest.title}"
    label = hud_font.render(text, True, (255, 255, 255))
    x = surface.get_width() // 2 - label.get_width() // 2
    y = surface.get_height() - 70

    bg = pygame.Surface((label.get_width() + 24, label.get_height() + 14))
    bg.set_alpha(180)
    bg.fill((20, 20, 20))
    surface.blit(bg, (x - 12, y - 7))
    surface.blit(label, (x, y))


def _draw_fill_hint(surface, hud_font, world, player_pos):
    if player_pos is None or world.terrain is None:
        return

    col, row = world_to_tile(player_pos.x, player_pos.y)
    if world.terrain.get(col, row) != "water":
        return

    label = hud_font.render("Press F to fill this water tile with dirt", True, (255, 255, 255))
    x = surface.get_width() // 2 - label.get_width() // 2
    y = surface.get_height() - 120

    bg = pygame.Surface((label.get_width() + 24, label.get_height() + 14))
    bg.set_alpha(180)
    bg.fill((20, 20, 20))
    surface.blit(bg, (x - 12, y - 7))
    surface.blit(label, (x, y))


def _draw_harvest_hint(surface, hud_font, resource_entity):
    if resource_entity is None:
        return
    harvestable = resource_entity.get_component(Harvestable)
    text = f"Press E to harvest {harvestable.resource_type}: {resource_entity.name}"
    label = hud_font.render(text, True, (255, 255, 255))
    x = surface.get_width() // 2 - label.get_width() // 2
    y = surface.get_height() - 70

    bg = pygame.Surface((label.get_width() + 24, label.get_height() + 14))
    bg.set_alpha(180)
    bg.fill((20, 20, 20))
    surface.blit(bg, (x - 12, y - 7))
    surface.blit(label, (x, y))


def _draw_plant_hint(surface, hud_font, world, player, player_pos):
    if player is None or player_pos is None:
        return
    inventory = player.get_component(Inventory)
    if inventory is None or inventory.items.get("seed", 0) < 1:
        return
    if world.terrain is not None:
        col, row = world_to_tile(player_pos.x, player_pos.y)
        if world.terrain.get(col, row) != world.terrain.default:
            return

    label = hud_font.render("Press P to plant a tree", True, (255, 255, 255))
    x = surface.get_width() // 2 - label.get_width() // 2
    y = surface.get_height() - 170

    bg = pygame.Surface((label.get_width() + 24, label.get_height() + 14))
    bg.set_alpha(180)
    bg.fill((20, 20, 20))
    surface.blit(bg, (x - 12, y - 7))
    surface.blit(label, (x, y))


MAP_TILE_COLORS = {
    "water": (58, 122, 190),
    "dirt": (122, 92, 56),
}
MAP_DEFAULT_COLOR = (86, 140, 74)


def _draw_map_overlay(surface, hud_font, world, player_pos):
    """Only ever draws world.loaded_chunks - chunks the procedural
    generator has actually filled in because a player got near them.
    Undiscovered land is generated on demand (core/worldgen.py) and simply
    isn't in that set yet, so it isn't drawn here either."""
    if player_pos is None:
        return

    x0, y0, panel_w, panel_h = _centered_panel(surface, 0.8, 0.8)

    title = hud_font.render(
        f"Explored map - {len(world.loaded_chunks)} chunks discovered (M to close)",
        True, (255, 255, 255),
    )
    surface.blit(title, (x0 + 12, y0 + 10))

    if not world.loaded_chunks:
        return

    cell = 12
    cx, cy = x0 + panel_w // 2, y0 + panel_h // 2 + 20
    player_chunk = chunk_of(*world_to_tile(player_pos.x, player_pos.y), CHUNK_SIZE)

    for (chx, chy) in world.loaded_chunks:
        dx, dy = chx - player_chunk[0], chy - player_chunk[1]
        px, py = cx + dx * cell, cy + dy * cell
        if not (x0 <= px <= x0 + panel_w - cell and y0 + 40 <= py <= y0 + panel_h - cell):
            continue

        sample_col = chx * CHUNK_SIZE + CHUNK_SIZE // 2
        sample_row = chy * CHUNK_SIZE + CHUNK_SIZE // 2
        tile_type = world.terrain.get(sample_col, sample_row) if world.terrain else "grass"
        color = MAP_TILE_COLORS.get(tile_type, MAP_DEFAULT_COLOR)
        pygame.draw.rect(surface, color, (px, py, cell - 1, cell - 1))

    pygame.draw.circle(surface, (230, 60, 60), (cx, cy), 5)
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 5, width=1)


def _format_recipe_line(number: int, name: str, recipe: dict, inventory) -> str:
    inputs_text = ", ".join(f"{item} x{qty:g}" for item, qty in recipe["inputs"].items())
    afford = all(
        (inventory.items.get(item, 0) if inventory else 0) >= qty
        for item, qty in recipe["inputs"].items()
    )
    nearby_note = f"  [needs nearby {recipe['requires_nearby']}]" if recipe.get("requires_nearby") else ""
    mark = "" if afford else "  (not enough materials)"
    return f"{number}) {name} - {inputs_text}{nearby_note}{mark}"


def _draw_build_menu(surface, hud_font, world, player_name, recipes):
    player = world.get_entity_by_name(player_name)
    inventory = player.get_component(Inventory) if player else None

    names = sorted(recipes.keys())
    lines = [
        _format_recipe_line(i + 1, name, recipes[name], inventory)
        for i, name in enumerate(names)
    ] or ["(no recipes known)"]
    lines.append("")
    lines.append("Press the number key to craft it.")

    _draw_titled_panel(surface, hud_font, "Build menu (B to close)", lines, height_ratio=0.7)


def draw_world(
    surface, font, hud_font, world, config,
    paused: bool = False, time_scale: float = 1.0,
    player_name: str = "Player1", controls_hint=DEFAULT_CONTROLS_HINT,
    show_help: bool = True, show_map: bool = False,
    show_inventory: bool = False, show_build_menu: bool = False, recipes=None,
):
    player = world.get_entity_by_name(player_name)
    player_pos = player.get_component(Position) if player else None
    camera = compute_camera(player_pos, surface.get_size()) if player_pos else (0, 0)

    surface.fill(sky_color(world, config))
    _draw_terrain(surface, world, config, camera)

    for entity in world.entities.values():
        pos = entity.get_component(Position)
        if pos is None:
            continue
        x, y = int(pos.x - camera[0]), int(pos.y - camera[1])

        if entity.has_component(Energy):
            _draw_living_entity(surface, font, x, y, entity)
        elif entity.has_component(Thermal):
            _draw_thermal_entity(surface, font, x, y, entity)
        else:
            renderable = entity.get_component(Renderable)
            kind = renderable.kind if renderable else "prop"
            drawer = _PROP_DRAWERS.get(kind, _draw_generic_prop)
            drawer(surface, font, x, y, entity)
            _draw_harvestable_bar(surface, x, y, entity)

    _draw_status_bar(surface, hud_font, world, config, paused, time_scale)
    _draw_player_panel(surface, font, world, player_name)

    nearby_quest = find_interactable_quest(world, player_pos)
    if nearby_quest is not None:
        _draw_interact_hint(surface, hud_font, nearby_quest)
    else:
        _draw_harvest_hint(surface, hud_font, find_interactable_resource(world, player_pos))
    _draw_fill_hint(surface, hud_font, world, player_pos)
    _draw_plant_hint(surface, hud_font, world, player, player_pos)

    if show_help:
        _draw_controls_help(surface, hud_font, controls_hint)
    if show_inventory:
        _draw_inventory_panel(surface, hud_font, world, player_name)
    if show_build_menu:
        _draw_build_menu(surface, hud_font, world, player_name, recipes or {})
    if show_map:
        _draw_map_overlay(surface, hud_font, world, player_pos)
