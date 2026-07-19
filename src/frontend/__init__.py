"""The graphics layer ("Kroppen"). Reads World state and renders it with
Pygame; contains no simulation logic - that lives entirely in src/owo/ and
src/server/. play.py never runs a SimulationEngine itself (single-player is
just a self-hosted GameServer, see play.py) - it only ever sends input
through NetworkClient and renders whatever World snapshot comes back, so it
can be swapped for another graphics backend without touching the
simulation core or the server.
"""
