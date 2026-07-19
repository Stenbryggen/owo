from src.owo.components.npc_profile import NpcProfile
from src.owo.components.relationships import Relationships
from src.owo.core.registry import register_system
from src.owo.core.systems import System


@register_system("npc_autonomy")
class NpcAutonomySystem(System):
    """Purely event-driven: every "new_day" (published by TimeSeasonSystem),
    each NPC's AI brain picks its action for the day via AIProvider. Nothing
    to do on the regular per-tick update()."""

    def setup(self, world, events, ai_provider):
        self._world = world
        self._ai_provider = ai_provider
        events.subscribe("new_day", self._on_new_day)

    def update(self, world, config, events, dt):
        pass

    def _on_new_day(self, payload):
        for entity in list(self._world.entities.values()):
            profile = entity.get_component(NpcProfile)
            if profile is None:
                continue

            relationships = entity.get_component(Relationships)
            context = {
                "entity": entity.name,
                "occupation": profile.occupation,
                "day": payload.get("day"),
                "friendship": dict(relationships.friendship) if relationships else {},
            }

            decision = self._ai_provider.generate_npc_decision(context)
            profile.current_goal = decision.get("action", profile.current_goal)
