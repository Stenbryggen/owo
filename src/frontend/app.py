import pygame

from src.frontend import renderer
from src.main import build_default_engine

DEFAULT_HOURS_PER_SECOND = 0.5  # 1 real second = 0.5 in-game hours -> a full day takes 48s


def run():
    pygame.init()
    pygame.display.set_caption("AI World Simulator")
    screen = pygame.display.set_mode(renderer.SCREEN_SIZE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    hud_font = pygame.font.SysFont(None, 36)

    engine = build_default_engine()

    paused = False
    time_scale = DEFAULT_HOURS_PER_SECOND

    running = True
    while running:
        dt_ms = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    time_scale = min(time_scale * 2, 16.0)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    time_scale = max(time_scale / 2, 0.03125)

        if not paused:
            engine.update((dt_ms / 1000.0) * time_scale)

        renderer.draw_world(screen, font, hud_font, engine, paused=paused, time_scale=time_scale)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run()
