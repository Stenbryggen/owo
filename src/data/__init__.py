"""Save-game persistence. See save_manager.py: save_world/load_world read and
write World snapshots to a SQLite database (one row per named slot, JSON
blob per row), built on src/owo/core/serialization.py. State only touches
SQLite on explicit save/load and periodic server autosave, never per tick -
the live World stays in RAM the rest of the time.
"""
