import math

import pygame

from src.frontend import renderer
from src.main import build_default_engine
from src.owo.components.position import Position

DEFAULT_HOURS_PER_SECOND = 0.5  # 1 real second = 0.5 in-game hours -> a full day takes 48s
PLAYER_SPEED = 260.0  # world units per second


def _movement_input():
    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
    dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
    if dx and dy:
        norm = math.sqrt(2) / 2
        dx, dy = dx * norm, dy * norm
    return dx, dy


def run():
    pygame.init()
    pygame.display.set_caption("AI World Simulator")
    screen = pygame.display.set_mode(renderer.SCREEN_SIZE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    hud_font = pygame.font.SysFont(None, 36)

    engine = build_default_engine()
    player = engine.world.get_entity_by_name("Player1")
    player_pos = player.get_component(Position) if player else None

    engine.events.subscribe(
        "quest_completed",
        lambda p: print(f"Quest completed: {p['quest']} (by {', '.join(p['contributors'])})"),
    )
    engine.events.subscribe(
        "leveled_up",
        lambda p: print(f"Level up! {p['entity']} is now level {p['level']} in {p['skill']}"),
    )

    paused = False
    time_scale = DEFAULT_HOURS_PER_SECOND

    running = True
    while running:
        dt_ms = clock.tick(60)
        dt_seconds = dt_ms / 1000.0

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

        if player_pos is not None:
            dx, dy = _movement_input()
            player_pos.x = max(0, min(renderer.WORLD_SIZE[0], player_pos.x + dx * PLAYER_SPEED * dt_seconds))
            player_pos.y = max(0, min(renderer.WORLD_SIZE[1], player_pos.y + dy * PLAYER_SPEED * dt_seconds))

        if not paused:
            engine.update(dt_seconds * time_scale)

            if player is not None and pygame.key.get_pressed()[pygame.K_e]:
                quest_entity = renderer.find_interactable_quest(engine.world, player_pos)
                if quest_entity is not None:
                    engine.perform_work(player.name, quest_entity.name, dt_seconds * time_scale)

        renderer.draw_world(screen, font, hud_font, engine, paused=paused, time_scale=time_scale)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run()
