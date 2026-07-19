"""The wire protocol between game_server.py and frontend/network_client.py:
newline-delimited JSON over a plain TCP socket. Kept tiny and stdlib-only
on purpose - one message per line, both directions.

Client -> Server:
  {"type": "join", "name": "<requested name>"}                  - first message
  {"type": "input", "dx": -1..1, "dy": -1..1, "work": bool, "fill": bool}
  {"type": "save"}                                               - persist the world now
  {"type": "load"}                                               - replace the world with the last save

Server -> Client:
  {"type": "welcome", "player_name": "<assigned name>", "config": {...}}
  {"type": "state", "world": {...world_to_dict output...}}
"""

import json
import socket


def send_message(sock: socket.socket, message: dict) -> None:
    sock.sendall((json.dumps(message) + "\n").encode("utf-8"))


def read_message(file) -> dict | None:
    line = file.readline()
    if not line:
        return None
    line = line.strip()
    if not line:
        return {}
    return json.loads(line)
