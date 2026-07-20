import socket
import threading

from src.owo.core import registry
from src.owo.core.serialization import world_from_dict
from src.server.protocol import read_message, send_message

# world_from_dict() needs every component type registered before it can
# deserialize a snapshot, but the client never builds a SimulationEngine
# (which normally does this) - it only ever reads snapshots.
registry.discover_and_import("src.owo.components")


class NetworkClient:
    """Thin client: never runs its own SimulationEngine, whether it's
    talking to a remote server or one play.py started locally for a
    single-player session. Sends input, receives a full world snapshot
    every server tick, and hands that straight to the renderer - the same
    World/Component classes and the same draw_world() every frontend uses."""

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
        self.recipes = welcome.get("recipes", {})

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

    def send_input(self, dx: float, dy: float, work: bool, fill: bool, plant: bool = False) -> None:
        self._send({"type": "input", "dx": dx, "dy": dy, "work": work, "fill": fill, "plant": plant})

    def send_save(self) -> None:
        self._send({"type": "save"})

    def send_load(self) -> None:
        self._send({"type": "load"})

    def send_craft(self, recipe_name: str) -> None:
        self._send({"type": "craft", "recipe": recipe_name})

    def send_eat(self) -> None:
        self._send({"type": "eat"})

    def _send(self, message: dict) -> None:
        try:
            send_message(self.sock, message)
        except OSError:
            self.connected = False
