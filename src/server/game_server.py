import json
import socket
import threading
import time
from pathlib import Path

from src.owo.components.position import Position
from src.owo.core.engine import SimulationEngine
from src.owo.core.interaction import find_interactable_quest
from src.owo.core.movement import speed_multiplier
from src.owo.core.players import spawn_player
from src.owo.core.serialization import world_to_dict
from src.owo.core.terrain import TILE_SIZE
from src.server.protocol import read_message, send_message

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "world.json"
CONTENT_DIR = REPO_ROOT / "content" / "entities"
PLAYER_TEMPLATE = CONTENT_DIR / "player.json"

TICK_HZ = 15
HOURS_PER_SECOND = 0.5  # matches the single-player app's default pace
PLAYER_SPEED = 260.0
FILL_COOLDOWN = 0.2


class ClientSession:
    def __init__(self, sock: socket.socket, name: str):
        self.sock = sock
        self.name = name
        self.dx = 0.0
        self.dy = 0.0
        self.work = False
        self.fill = False
        self.fill_timer = 0.0


class GameServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.engine = SimulationEngine(str(CONFIG_PATH), str(CONTENT_DIR))
        self.clients: dict[str, ClientSession] = {}
        self._lock = threading.Lock()
        self._next_spawn_index = 1  # spawn_index 0 is content/entities/player.json's own spot
        self.ready = threading.Event()  # set once the listening socket is bound; lets tests use port=0
        self._stop_event = threading.Event()
        self._server_sock = None

        self.engine.events.subscribe(
            "quest_completed",
            lambda p: print(f"[server] Quest completed: {p['quest']} (by {', '.join(p['contributors'])})"),
        )
        self.engine.events.subscribe(
            "leveled_up",
            lambda p: print(f"[server] Level up! {p['entity']} is now level {p['level']} in {p['skill']}"),
        )

    def start(self) -> None:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.host, self.port))
        self.port = server_sock.getsockname()[1]
        server_sock.settimeout(0.5)  # periodic wakeup so stop() is noticed promptly
        server_sock.listen()
        self._server_sock = server_sock
        print(f"[server] listening on {self.host}:{self.port}")

        threading.Thread(target=self._tick_loop, daemon=True).start()
        self.ready.set()

        try:
            while not self._stop_event.is_set():
                try:
                    client_sock, addr = server_sock.accept()
                except socket.timeout:
                    continue
                threading.Thread(
                    target=self._handle_client, args=(client_sock, addr), daemon=True
                ).start()
        except KeyboardInterrupt:
            print("[server] shutting down")
        finally:
            server_sock.close()

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            for session in self.clients.values():
                try:
                    session.sock.close()
                except OSError:
                    pass

    def _unique_name(self, requested: str) -> str:
        name = requested or "Player"
        suffix = 1
        while self.engine.world.get_entity_by_name(name) is not None:
            suffix += 1
            name = f"{requested}{suffix}"
        return name

    def _handle_client(self, sock: socket.socket, addr) -> None:
        name = None
        file = sock.makefile("r")
        try:
            join_msg = read_message(file)
            if not join_msg or join_msg.get("type") != "join":
                return

            with self._lock:
                name = self._unique_name(join_msg.get("name", "Player"))
                spawn_index = self._next_spawn_index
                self._next_spawn_index += 1
                spawn_player(self.engine.world, str(PLAYER_TEMPLATE), name, spawn_index)
                self.clients[name] = ClientSession(sock, name)

            send_message(sock, {
                "type": "welcome", "player_name": name, "config": self.engine.config,
            })
            print(f"[server] {name} joined from {addr}")

            while True:
                msg = read_message(file)
                if msg is None:
                    break
                if msg.get("type") == "input":
                    with self._lock:
                        session = self.clients.get(name)
                        if session is not None:
                            session.dx = float(msg.get("dx", 0.0))
                            session.dy = float(msg.get("dy", 0.0))
                            session.work = bool(msg.get("work", False))
                            session.fill = bool(msg.get("fill", False))
        except (ConnectionResetError, BrokenPipeError, OSError, json.JSONDecodeError):
            pass
        finally:
            self._disconnect(name)

    def _disconnect(self, name: str | None) -> None:
        if name is None:
            return
        with self._lock:
            session = self.clients.pop(name, None)
            entity = self.engine.world.get_entity_by_name(name)
            if entity is not None:
                self.engine.world.entities.pop(entity.id, None)
        if session is not None:
            print(f"[server] {name} disconnected")

    def _tick_loop(self) -> None:
        dt_real = 1.0 / TICK_HZ
        dt_hours = dt_real * HOURS_PER_SECOND

        while not self._stop_event.is_set():
            start = time.monotonic()

            with self._lock:
                self.engine.update(dt_hours)

                world_width = self.engine.world.terrain.width * TILE_SIZE
                world_height = self.engine.world.terrain.height * TILE_SIZE

                for name, session in list(self.clients.items()):
                    entity = self.engine.world.get_entity_by_name(name)
                    pos = entity.get_component(Position) if entity else None
                    if pos is None:
                        continue

                    speed = PLAYER_SPEED * speed_multiplier(self.engine.world, pos)
                    pos.x = max(0, min(world_width, pos.x + session.dx * speed * dt_real))
                    pos.y = max(0, min(world_height, pos.y + session.dy * speed * dt_real))

                    if session.work:
                        quest = find_interactable_quest(self.engine.world, pos)
                        if quest is not None:
                            self.engine.perform_work(name, quest.name, dt_hours)

                    session.fill_timer -= dt_real
                    if session.fill and session.fill_timer <= 0:
                        if self.engine.fill_terrain_tile(pos.x, pos.y):
                            session.fill_timer = FILL_COOLDOWN

                snapshot = {"type": "state", "world": world_to_dict(self.engine.world)}
                recipients = list(self.clients.items())

            self._broadcast(snapshot, recipients)

            elapsed = time.monotonic() - start
            time.sleep(max(0.0, dt_real - elapsed))

    def _broadcast(self, message: dict, recipients) -> None:
        for name, session in recipients:
            try:
                send_message(session.sock, message)
            except OSError:
                self._disconnect(name)


if __name__ == "__main__":
    GameServer().start()
