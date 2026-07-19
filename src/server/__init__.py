"""The multiplayer game server. Owns the one authoritative SimulationEngine
("Hjernen") and lets several thin pygame clients ("Kroppen", see
src/frontend/multiplayer_app.py) connect over a plain TCP/JSON protocol -
each client only sends input and receives world snapshots, never runs its
own copy of the simulation. This is what makes "time can't be paused just
because one player is asleep" (doc §3) actually true: the server ticks
continuously regardless of what any single client is doing.
"""
