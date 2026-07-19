from src.owo.components.energy import Energy
from src.owo.components.sleep import Sleep
from src.owo.core.registry import register_system
from src.owo.core.systems import System


@register_system("sleep_recovery")
class SleepRecoverySystem(System):
    required_components = (Sleep, Energy)

    def update(self, world, config, events, dt):
        seasonal = config["world"]["seasonal_factors"][world.current_season]
        night_length = seasonal["night_length_hours"]
        is_night = world.current_time < night_length
        base_recovery = config["player_base_stats"]["recovery_rate_base"]

        for entity in world.get_entities_with_components(Sleep, Energy):
            sleep = entity.get_component(Sleep)
            energy = entity.get_component(Energy)

            if not sleep.is_sleeping:
                continue

            if is_night:
                rate = sleep.recovery_rate if sleep.recovery_rate is not None else base_recovery
                energy.current = min(energy.max_energy, energy.current + rate * dt)
                events.publish(
                    "sleep_recovery_applied", {"entity": entity.name, "amount": rate * dt}
                )
            else:
                sleep.is_sleeping = False
                events.publish("sleep_ended", {"entity": entity.name})
