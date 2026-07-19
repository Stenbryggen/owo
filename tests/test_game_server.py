import json
import socket
import threading
import time

import pytest

from src.data.save_manager import load_world as sqlite_load_world
from src.server.game_server import GameServer


@pytest.fixture
def make_server(tmp_path):
    created = []

    def _make(**kwargs):
        kwargs.setdefault("db_path", str(tmp_path / "world.db"))
        kwargs.setdefault("autosave_interval_seconds", 9999.0)  # opt-in per test
        srv = GameServer(host="127.0.0.1", port=0, **kwargs)
        threading.Thread(target=srv.start, daemon=True).start()
        assert srv.ready.wait(timeout=2), "server did not start in time"
        created.append(srv)
        return srv

    yield _make

    for srv in created:
        srv.stop()


@pytest.fixture
def server(make_server):
    return make_server()


def _connect(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", port))
    return sock, sock.makefile("r")


def _send(sock, msg):
    sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))


def _recv(file):
    line = file.readline()
    return json.loads(line) if line else None


def _close(sock, file):
    # makefile() dups the fd, so sock.close() alone leaves the connection
    # open (and the server's blocking readline() unblocked) until that dup
    # is also closed. shutdown() tears down the TCP connection outright.
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    file.close()
    sock.close()


def _position_x(state_msg, entity_name):
    entity = next(e for e in state_msg["world"]["entities"] if e["name"] == entity_name)
    return next(c["params"]["x"] for c in entity["components"] if c["type"] == "position")


def _position_x_from_world(world, entity_name):
    from src.owo.components.position import Position

    return world.get_entity_by_name(entity_name).get_component(Position).x


def test_two_clients_with_same_requested_name_get_deduped(server):

    sock_a, file_a = _connect(server.port)
    _send(sock_a, {"type": "join", "name": "Alice"})
    welcome_a = _recv(file_a)

    sock_b, file_b = _connect(server.port)
    _send(sock_b, {"type": "join", "name": "Alice"})
    welcome_b = _recv(file_b)

    assert welcome_a["player_name"] == "Alice"
    assert welcome_b["player_name"] != "Alice"
    assert welcome_b["player_name"].startswith("Alice")

    _close(sock_a, file_a)
    _close(sock_b, file_b)


def test_welcome_includes_world_config(server):
    sock, file = _connect(server.port)
    _send(sock, {"type": "join", "name": "Configged"})
    welcome = _recv(file)

    assert "world" in welcome["config"]
    assert "synergy" in welcome["config"]
    _close(sock, file)


def test_movement_input_moves_the_players_authoritative_position(server):
    sock, file = _connect(server.port)
    _send(sock, {"type": "join", "name": "Mover"})
    name = _recv(file)["player_name"]

    first_state = _recv(file)
    start_x = _position_x(first_state, name)

    _send(sock, {"type": "input", "dx": 1.0, "dy": 0.0, "work": False, "fill": False})

    latest = first_state
    for _ in range(10):  # ~0.7s of ticks at 15Hz - guaranteed to arrive since the server ticks continuously
        msg = _recv(file)
        if msg is not None:
            latest = msg

    end_x = _position_x(latest, name)
    assert end_x > start_x

    _close(sock, file)


def test_disconnect_removes_the_player_entity_from_the_world(server):
    sock, file = _connect(server.port)
    _send(sock, {"type": "join", "name": "Ghost"})
    name = _recv(file)["player_name"]

    time.sleep(0.2)
    assert server.engine.world.get_entity_by_name(name) is not None

    _close(sock, file)

    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        if server.engine.world.get_entity_by_name(name) is None:
            break
        time.sleep(0.1)

    assert server.engine.world.get_entity_by_name(name) is None


def test_two_players_see_each_other_in_the_shared_world(server):

    sock_a, file_a = _connect(server.port)
    _send(sock_a, {"type": "join", "name": "A"})
    _recv(file_a)

    sock_b, file_b = _connect(server.port)
    _send(sock_b, {"type": "join", "name": "B"})
    _recv(file_b)

    time.sleep(0.2)
    state = _recv(file_a)
    names = {e["name"] for e in state["world"]["entities"]}

    assert "A" in names
    assert "B" in names

    _close(sock_a, file_a)
    _close(sock_b, file_b)


def test_save_message_persists_the_world_to_sqlite(make_server, tmp_path):
    db_path = str(tmp_path / "save_test.db")
    srv = make_server(db_path=db_path)

    sock, file = _connect(srv.port)
    _send(sock, {"type": "join", "name": "Saver"})
    name = _recv(file)["player_name"]
    _recv(file)  # first state broadcast

    _send(sock, {"type": "input", "dx": 1.0, "dy": 0.0, "work": False, "fill": False})
    time.sleep(0.3)

    _send(sock, {"type": "save"})
    time.sleep(0.2)

    saved_world = sqlite_load_world(db_path)
    assert saved_world is not None
    assert saved_world.get_entity_by_name(name) is not None

    _close(sock, file)


def test_load_message_restores_previously_saved_position(make_server, tmp_path):
    db_path = str(tmp_path / "load_test.db")
    srv = make_server(db_path=db_path)

    sock, file = _connect(srv.port)
    _send(sock, {"type": "join", "name": "Loader"})
    name = _recv(file)["player_name"]
    first_state = _recv(file)
    x_at_join = _position_x(first_state, name)

    _send(sock, {"type": "input", "dx": 1.0, "dy": 0.0, "work": False, "fill": False})
    time.sleep(0.3)
    _send(sock, {"type": "save"})
    time.sleep(0.2)

    saved_world = sqlite_load_world(db_path)
    x_at_save = _position_x_from_world(saved_world, name)
    assert x_at_save > x_at_join

    time.sleep(0.3)  # keep moving after the save
    _send(sock, {"type": "input", "dx": 0.0, "dy": 0.0, "work": False, "fill": False})

    _send(sock, {"type": "load"})
    time.sleep(0.3)  # let the server actually process the load before we check

    latest = None
    for _ in range(20):
        msg = _recv(file)
        if msg is not None:
            latest = msg
    x_after_load = _position_x(latest, name)

    assert x_after_load == pytest.approx(x_at_save, abs=1.0)

    _close(sock, file)


def test_autosave_persists_periodically(make_server, tmp_path):
    db_path = str(tmp_path / "autosave_test.db")
    srv = make_server(db_path=db_path, autosave_interval_seconds=0.3)

    sock, file = _connect(srv.port)
    _send(sock, {"type": "join", "name": "Auto"})
    name = _recv(file)["player_name"]
    _recv(file)

    _send(sock, {"type": "input", "dx": 1.0, "dy": 0.0, "work": False, "fill": False})

    deadline = time.monotonic() + 3.0
    saved = None
    while time.monotonic() < deadline:
        saved = sqlite_load_world(db_path)
        if saved is not None and saved.get_entity_by_name(name) is not None:
            break
        time.sleep(0.1)

    assert saved is not None
    assert saved.get_entity_by_name(name) is not None

    _close(sock, file)


def test_new_server_picks_up_a_previously_saved_world(make_server, tmp_path):
    db_path = str(tmp_path / "restart_test.db")
    srv_a = make_server(db_path=db_path)

    sock, file = _connect(srv_a.port)
    _send(sock, {"type": "join", "name": "Persistent"})
    name = _recv(file)["player_name"]
    _recv(file)
    _send(sock, {"type": "input", "dx": 1.0, "dy": 0.0, "work": False, "fill": False})
    time.sleep(0.3)
    _send(sock, {"type": "save"})
    time.sleep(0.2)
    _close(sock, file)
    srv_a.stop()

    srv_b = make_server(db_path=db_path)
    assert srv_b.engine.world.get_entity_by_name(name) is not None
