import pygame

from src.owo.components.energy import Energy
from src.owo.components.health import Health
from src.owo.components.sleep import Sleep
from src.owo.components.thermal import Thermal

SCREEN_SIZE = (900, 500)
GROUND_Y = 320
ENTITY_RADIUS = 30
ENTITY_SPACING = 220
ENTITY_START_X = 150

BAR_WIDTH = 60
BAR_HEIGHT = 8

DAY_BG = (135, 196, 235)
NIGHT_BG = (18, 24, 48)
SEASON_TINT = {
    "Winter": (210, 225, 245),
    "Summer": (255, 244, 200),
    "Spring": (215, 245, 210),
    "Autumn": (245, 220, 180),
}


def is_night(world, config) -> bool:
    seasonal = config["world"]["seasonal_factors"][world.current_season]
    return world.current_time < seasonal["night_length_hours"]


def _blend(base, tint, amount=0.15):
    return tuple(int(base[i] + (tint[i] - base[i]) * amount) for i in range(3))


def background_color(world, config):
    base = NIGHT_BG if is_night(world, config) else DAY_BG
    tint = SEASON_TINT.get(world.current_season, base)
    return _blend(base, tint)


def _bar(surface, x, y, ratio, color):
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(surface, (40, 40, 40), (x, y, BAR_WIDTH, BAR_HEIGHT), border_radius=2)
    pygame.draw.rect(surface, color, (x, y, int(BAR_WIDTH * ratio), BAR_HEIGHT), border_radius=2)


def _draw_living_entity(surface, font, x, entity):
    energy = entity.get_component(Energy)
    health = entity.get_component(Health)
    sleep = entity.get_component(Sleep)

    color = (90, 140, 220)
    if health and health.is_sick:
        color = (150, 90, 190)
    if sleep and sleep.is_sleeping:
        color = (70, 90, 150)

    pygame.draw.circle(surface, color, (x, GROUND_Y), ENTITY_RADIUS)
    pygame.draw.circle(surface, (20, 20, 20), (x, GROUND_Y), ENTITY_RADIUS, width=2)

    label = font.render(entity.name, True, (20, 20, 20))
    surface.blit(label, label.get_rect(center=(x, GROUND_Y - ENTITY_RADIUS - 16)))

    bar_x = x - BAR_WIDTH // 2
    if energy:
        _bar(surface, bar_x, GROUND_Y + ENTITY_RADIUS + 10,
             energy.current / energy.max_energy, (90, 200, 90))
    if health:
        _bar(surface, bar_x, GROUND_Y + ENTITY_RADIUS + 22,
             health.current / health.max_health, (210, 70, 70))

    if sleep and sleep.is_sleeping:
        zzz = font.render("Zzz", True, (230, 230, 255))
        surface.blit(zzz, (x + ENTITY_RADIUS - 5, GROUND_Y - ENTITY_RADIUS - 40))


def _draw_thermal_entity(surface, font, x, entity):
    flicker = 4 if (pygame.time.get_ticks() // 200) % 2 == 0 else 0
    pygame.draw.polygon(
        surface,
        (240, 120, 30),
        [(x, GROUND_Y - 26 - flicker), (x - 16, GROUND_Y + 10), (x + 16, GROUND_Y + 10)],
    )
    label = font.render(entity.name, True, (20, 20, 20))
    surface.blit(label, label.get_rect(center=(x, GROUND_Y - ENTITY_RADIUS - 16)))


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
        "SPACE=pause  +/-=speed  ESC=quit",
    ]
    for i, text in enumerate(lines):
        label = hud_font.render(text, True, (15, 15, 15))
        surface.blit(label, (12, 10 + i * 22))


def draw_world(surface, font, hud_font, engine, paused: bool = False, time_scale: float = 1.0):
    world, config = engine.world, engine.config

    surface.fill(background_color(world, config))
    pygame.draw.rect(
        surface, (60, 110, 50),
        (0, GROUND_Y + ENTITY_RADIUS + 30, surface.get_width(), 200),
    )

    x = ENTITY_START_X
    for entity in world.entities.values():
        if entity.has_component(Energy):
            _draw_living_entity(surface, font, x, entity)
        elif entity.has_component(Thermal):
            _draw_thermal_entity(surface, font, x, entity)
        else:
            continue
        x += ENTITY_SPACING

    _draw_hud(surface, hud_font, world, config, paused, time_scale)
