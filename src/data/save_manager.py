import json
import sqlite3
from pathlib import Path
from typing import Optional

from src.owo.core.ecs import World
from src.owo.core.serialization import world_from_dict, world_to_dict

DEFAULT_SLOT = "default"


def init_db(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS saves (
            slot TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def save_world(world: World, path: str, slot: str = DEFAULT_SLOT) -> None:
    conn = init_db(path)
    try:
        data = json.dumps(world_to_dict(world))
        conn.execute(
            """
            INSERT INTO saves (slot, data, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(slot) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at
            """,
            (slot, data),
        )
        conn.commit()
    finally:
        conn.close()


def load_world(path: str, slot: str = DEFAULT_SLOT) -> Optional[World]:
    if not Path(path).exists():
        return None

    conn = init_db(path)
    try:
        row = conn.execute("SELECT data FROM saves WHERE slot = ?", (slot,)).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return world_from_dict(json.loads(row[0]))
