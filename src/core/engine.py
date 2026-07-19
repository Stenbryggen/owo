import json
import os
from .ecs import World, EnergyComponent, HealthComponent, ThermalComponent

class SimulationEngine:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.world = World()
        self.current_time = 0.0  # In hours
        self.current_season = self.config["world"]["seasons"][0]
        self.day_count = 0

    def _load_config(self, path: str) -> dict:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found at {path}")
        with open(path, 'r') as f:
            return json.load(f)

    def update(self, delta_time_hours: float):
        # Update world time
        self.current_time += delta_time_hours * self.config["world"]["time_speed"]
        
        # Check for day/season transitions
        day_length = self.config["world"]["day_length_hours"]
        if self.current_time >= day_length:
            self.current_time -= day_length
            self.day_count += 1
            self._update_season()

        # Run systems
        self._energy_drain_system(delta_time_hours)
        self._sickness_system(delta_time_hours)

    def _update_season(self):
        # Simple season logic: change every 30 days
        seasons = self.config["world"]["seasons"]
        season_index = (self.day_count // 30) % len(seasons)
        self.current_season = seasons[season_index]

    def _energy_drain_system(self, dt: float):
        season_config = self.config["world"]["seasonal_factors"][self.current_season]
        drain_mult = season_config["energy_drain_multiplier"]
        
        entities = self.world.get_entities_with_components(EnergyComponent)
        for entity in entities:
            energy = entity.get_component(EnergyComponent)
            
            # Base drain (can be adjusted by activity)
            base_drain = 1.0 * drain_mult * dt
            
            # Reduce drain if near thermal source
            thermal = entity.get_component(ThermalComponent)
            if thermal:
                # Simple logic: heat source reduces drain
                base_drain = max(0.1, base_drain - (thermal.heat_source * 0.1))
            
            energy.current = max(0, energy.current - base_drain)

    def _sickness_system(self, dt: float):
        season_config = self.config["world"]["seasonal_factors"][self.current_season]
        base_risk = season_config["sickness_risk_base"]
        
        entities = self.world.get_entities_with_components(EnergyComponent, HealthComponent)
        for entity in entities:
            energy = entity.get_component(EnergyComponent)
            health = entity.get_component(HealthComponent)
            
            # Increase sickness risk if energy is low
            risk = base_risk
            if energy.current < 20:
                risk *= 2
            
            # Placeholder for random sickness check
            # In a real sim, we might use a random roll here
            if not health.is_sick and risk > 0.15: # Example threshold
                # health.is_sick = True
                pass
