import argparse
import math
import threading

import pygame

from src.frontend import renderer
from src.frontend.network_client import NetworkClient
from src.server.game_server import GameServer

CONTROLS_HINT = "WASD/arrows=move  E=work quest  F=fill water  F5=save F9=load  ESC=quit"


def _movement_input():
    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
    dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
    if dx and dy:
        norm = math.sqrt(2) / 2
        dx, dy = dx * norm, dy * norm
    return dx, dy


def _start_local_server() -> GameServer:
    server = GameServer(host="127.0.0.1", port=0)
    threading.Thread(target=server.start, daemon=True).start()
    if not server.ready.wait(timeout=5):
        raise RuntimeError("Local server did not start in time")
    return server


def run(host: str | None, port: int, name: str) -> None:
    """Single-player and multiplayer are the same code path: single-player
    is just a self-hosted server of one. host=None means "start a local
    GameServer and connect to it"; otherwise connect to that remote
    server. Either way, this is a thin NetworkClient - no local
    SimulationEngine, no duplicated movement/quest/terrain logic (that all
    lives once, authoritatively, in GameServer)."""
    pygame.init()
    pygame.display.set_caption(f"AI World Simulator - {name}")
    screen = pygame.display.set_mode(renderer.SCREEN_SIZE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    hud_font = pygame.font.SysFont(None, 36)

    local_server = None
    if host is None:
        local_server = _start_local_server()
        host, port = "127.0.0.1", local_server.port
        print(f"Hosting locally on {host}:{port}")

    client = NetworkClient(host, port, name)
    print(f"Connected as {client.player_name}")

    running = True
    while running and client.connected:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F5:
                    client.send_save()
                elif event.key == pygame.K_F9:
                    client.send_load()

        keys = pygame.key.get_pressed()
        dx, dy = _movement_input()
        client.send_input(dx, dy, keys[pygame.K_e], keys[pygame.K_f])

        world = client.get_world()
        if world is not None:
            renderer.draw_world(
                screen, font, hud_font, world, client.config,
                player_name=client.player_name, controls_hint=CONTROLS_HINT,
            )
            pygame.display.flip()

    pygame.quit()
    if local_server is not None:
        local_server.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="AI World Simulator")
    parser.add_argument(
        "--host", default=None,
        help="Connect to a remote server instead of self-hosting a local one",
    )
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--name", default="Player")
    args = parser.parse_args()
    run(args.host, args.port, args.name)


if __name__ == "__main__":
    main()
