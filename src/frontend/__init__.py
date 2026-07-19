"""The graphics layer ("Kroppen"). Reads World state and renders it with
Pygame; contains no simulation logic - that lives entirely in src/owo/. The
frontend only ever calls SimulationEngine.update() and reads components -
never mutates simulation state directly - so it can be swapped for another
graphics backend later without touching the simulation core.
"""
