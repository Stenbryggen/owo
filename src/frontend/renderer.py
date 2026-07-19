import math

import pygame

from src.owo.components.energy import Energy
from src.owo.components.health import Health
from src.owo.components.position import Position
from src.owo.components.quest import Quest
from src.owo.components.renderable import Renderable
from src.owo.components.skills import Skills
from src.owo.components.sleep import Sleep
from src.owo.components.thermal import Thermal
from src.owo.components.wallet import Wallet
from src.owo.core.work import quest_progress

SCREEN_SIZE = (1600, 900)
WORLD_SIZE = (2400, 1600)

ENTITY_RADIUS = 34
BAR_WIDTH = 90
BAR_HEIGHT = 14

INTERACT_RADIUS = 100
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
GROUND_PATCH_COLOR = (64, 115, 54)
GROUND_PATCHES = [(300, 900), (1200, 300), (2000, 1200), (700, 1400), (1800, 700)]


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


def compute_camera(player_pos, screen_size, world_size):
    cam_x = player_pos.x - screen_size[0] / 2
    cam_y = player_pos.y - screen_size[1] / 2
    cam_x = max(0, min(cam_x, max(0, world_size[0] - screen_size[0])))
    cam_y = max(0, min(cam_y, max(0, world_size[1] - screen_size[1])))
    return cam_x, cam_y


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
    "rock": _draw_rock,
    "quest_board": _draw_quest_board,
    "chest": _draw_chest,
    "quest_marker": _draw_quest_marker,
}


def find_interactable_quest(world, player_pos):
    """Nearest open/in-progress quest entity within INTERACT_RADIUS of
    player_pos, or None. Shared by the frontend's interact prompt and its
    "E to work" input handling so both agree on what's reachable."""
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


def _format_time(hours: float) -> str:
    h = int(hours) % 24
    m = int((hours - int(hours)) * 60)
    return f"{h:02d}:{m:02d}"


def _draw_hud(surface, hud_font, world, config, paused: bool, time_scale: float):
    night_label = "Night" if is_night(world, config) else "Day"
    lines = [
        f"Season: {world.current_season}  (Day {world.day_count})  {night_label}",
        f"Time: {_format_time(world.current_time)}    Speed: {time_scale:g}x"
        + ("  [PAUSED]" if paused else ""),
        "WASD/arrows=move  E=work quest  SPACE=pause  +/-=speed  ESC=quit",
    ]
    for i, text in enumerate(lines):
        label = hud_font.render(text, True, (15, 15, 15))
        bg = pygame.Surface(label.get_size())
        bg.set_alpha(140)
        bg.fill((255, 255, 255))
        surface.blit(bg, (16, 12 + i * 38))
        surface.blit(label, (20, 14 + i * 38))


def _draw_player_panel(surface, font, world):
    player = world.get_entity_by_name("Player1")
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


def draw_world(surface, font, hud_font, engine, paused: bool = False, time_scale: float = 1.0):
    world, config = engine.world, engine.config

    player = world.get_entity_by_name("Player1")
    player_pos = player.get_component(Position) if player else None
    camera = compute_camera(player_pos, SCREEN_SIZE, WORLD_SIZE) if player_pos else (0, 0)

    surface.fill(sky_color(world, config))
    patch_color = ground_tint(world, config)
    pygame.draw.rect(surface, patch_color, (-camera[0], -camera[1], *WORLD_SIZE))
    for px, py in GROUND_PATCHES:
        pygame.draw.circle(
            surface, GROUND_PATCH_COLOR, (int(px - camera[0]), int(py - camera[1])), 90
        )

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

    _draw_hud(surface, hud_font, world, config, paused, time_scale)
    _draw_player_panel(surface, font, world)
    _draw_interact_hint(surface, hud_font, find_interactable_quest(world, player_pos))
