"""The game server. Owns the one authoritative SimulationEngine ("Hjernen")
and lets any number of thin pygame clients ("Kroppen", see
src/frontend/play.py) connect over a plain TCP/JSON protocol - each client
only sends input and receives world snapshots, never runs its own copy of
the simulation. Single-player is just this same server self-hosted for one
client; there is no separate non-networked code path. This is also what
makes "time can't be paused just because one player is asleep" (doc §3)
actually true: the server ticks continuously regardless of what any single
client is doing.
"""
