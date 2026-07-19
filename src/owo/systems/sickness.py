import random

from src.owo.components.energy import Energy
from src.owo.components.health import Health
from src.owo.core.registry import register_system
from src.owo.core.systems import System


@register_system("sickness")
class SicknessSystem(System):
    required_components = (Energy, Health)

    def update(self, world, config, events, dt):
        seasonal = config["world"]["seasonal_factors"][world.current_season]
        base_risk = seasonal["sickness_risk_base"]

        for entity in world.get_entities_with_components(Energy, Health):
            energy = entity.get_component(Energy)
            health = entity.get_component(Health)

            risk = base_risk * 2 if energy.current < 20 else base_risk
            events.publish("sickness_risk_rolled", {"entity": entity.name, "risk": risk})

            if not health.is_sick and random.random() < risk:
                health.is_sick = True
                events.publish("entity_fell_sick", {"entity": entity.name})
