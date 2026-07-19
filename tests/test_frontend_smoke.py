import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402 - must come after SDL_VIDEODRIVER is set

from src.frontend import renderer  # noqa: E402
from src.main import build_default_engine  # noqa: E402


def test_render_loop_runs_headless():
    pygame.init()
    screen = pygame.display.set_mode(renderer.SCREEN_SIZE)
    font = pygame.font.SysFont(None, 32)
    hud_font = pygame.font.SysFont(None, 36)

    engine = build_default_engine()

    for _ in range(5):
        engine.update(1.0)
        renderer.draw_world(screen, font, hud_font, engine)

    pygame.quit()
