from src.owo.components.energy import Energy
from src.owo.components.thermal import Thermal
from src.owo.core.registry import register_system
from src.owo.core.systems import System


@register_system("energy_drain")
class EnergyDrainSystem(System):
    required_components = (Energy,)

    def update(self, world, config, events, dt):
        seasonal = config["world"]["seasonal_factors"][world.current_season]
        drain_mult = seasonal["energy_drain_multiplier"]

        for entity in world.get_entities_with_components(Energy):
            energy = entity.get_component(Energy)
            was_depleted = energy.current <= 0

            base_drain = 1.0 * drain_mult * dt
            thermal = entity.get_component(Thermal)
            if thermal:
                base_drain = max(0.1, base_drain - thermal.heat_source * 0.1)

            energy.current = max(0.0, energy.current - base_drain)

            if energy.current <= 0 and not was_depleted:
                events.publish("energy_depleted", {"entity": entity.name})
