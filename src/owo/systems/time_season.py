from src.owo.core.registry import register_system
from src.owo.core.systems import System


@register_system("time_season")
class TimeSeasonSystem(System):
    def update(self, world, config, events, dt):
        world_config = config["world"]
        world.current_time += dt * world_config["time_speed"]

        day_length = world_config["day_length_hours"]
        if world.current_time >= day_length:
            world.current_time -= day_length
            world.day_count += 1
            self._update_season(world, world_config, events)

    def _update_season(self, world, world_config, events):
        seasons = world_config["seasons"]
        new_season = seasons[(world.day_count // 30) % len(seasons)]
        if new_season != world.current_season:
            world.current_season = new_season
            events.publish("season_changed", {"season": new_season, "day": world.day_count})
