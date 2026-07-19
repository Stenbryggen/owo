from src.core.engine import SimulationEngine
from src.core.ecs import EnergyComponent, HealthComponent, ThermalComponent

def main():
    print("Initializing AI World Simulator...")
    engine = SimulationEngine("config/config.json")
    
    # Create a Player
    player = engine.world.create_entity("Player1")
    player.add_component(EnergyComponent(current=100.0))
    player.add_component(HealthComponent(current=100.0))
    
    # Create an NPC (Birk)
    birk = engine.world.create_entity("Birk")
    birk.add_component(EnergyComponent(current=80.0))
    birk.add_component(HealthComponent(current=100.0))
    
    # Create a Heat Source (Campfire)
    campfire = engine.world.create_entity("Campfire")
    campfire.add_component(ThermalComponent(heat_source=5.0))

    print(f"Start: Season={engine.current_season}, Time={engine.current_time:.2f}h")
    
    # Simulate 48 hours
    for i in range(48):
        engine.update(1.0) # 1 hour step
        if i % 12 == 0:
            p_energy = player.get_component(EnergyComponent).current
            b_energy = birk.get_component(EnergyComponent).current
            print(f"Hour {i}: Season={engine.current_season}, Player Energy={p_energy:.2f}, Birk Energy={b_energy:.2f}")

    print("Simulation complete.")

if __name__ == "__main__":
    main()
