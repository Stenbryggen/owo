import math
import socket
import sys
import threading

import pygame

from src.frontend import renderer
from src.owo.core.serialization import world_from_dict
from src.server.protocol import read_message, send_message

NETWORK_CONTROLS_HINT = "WASD/arrows=move  E=work quest  F=fill water  ESC=quit  (networked)"


class NetworkClient:
    """Thin client: never runs its own SimulationEngine. Sends input,
    receives a full world snapshot every server tick, and hands that
    straight to the renderer - the same World/Component classes and the
    same draw_world() the single-process app uses."""

    def __init__(self, host: str, port: int, name: str):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self._file = self.sock.makefile("r")

        send_message(self.sock, {"type": "join", "name": name})
        welcome = read_message(self._file)
        if not welcome or welcome.get("type") != "welcome":
            raise ConnectionError("Server did not send a welcome message")

        self.player_name = welcome["player_name"]
        self.config = welcome["config"]

        self._world = None
        self._lock = threading.Lock()
        self.connected = True
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def _recv_loop(self) -> None:
        try:
            while True:
                msg = read_message(self._file)
                if msg is None:
                    break
                if msg.get("type") == "state":
                    world = world_from_dict(msg["world"])
                    with self._lock:
                        self._world = world
        except (OSError, ValueError):
            pass
        finally:
            self.connected = False

    def get_world(self):
        with self._lock:
            return self._world

    def send_input(self, dx: float, dy: float, work: bool, fill: bool) -> None:
        try:
            send_message(self.sock, {"type": "input", "dx": dx, "dy": dy, "work": work, "fill": fill})
        except OSError:
            self.connected = False


def _movement_input():
    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
    dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
    if dx and dy:
        norm = math.sqrt(2) / 2
        dx, dy = dx * norm, dy * norm
    return dx, dy


def run(host: str = "127.0.0.1", port: int = 8765, name: str = "Player") -> None:
    pygame.init()
    pygame.display.set_caption(f"AI World Simulator - {name}")
    screen = pygame.display.set_mode(renderer.SCREEN_SIZE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    hud_font = pygame.font.SysFont(None, 36)

    client = NetworkClient(host, port, name)
    print(f"Connected as {client.player_name}")

    running = True
    while running and client.connected:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        dx, dy = _movement_input()
        client.send_input(dx, dy, keys[pygame.K_e], keys[pygame.K_f])

        world = client.get_world()
        if world is not None:
            renderer.draw_world(
                screen, font, hud_font, world, client.config,
                player_name=client.player_name, controls_hint=NETWORK_CONTROLS_HINT,
            )
            pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    name = sys.argv[3] if len(sys.argv) > 3 else "Player"
    run(host, port, name)
