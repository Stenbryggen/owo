from pathlib import Path

from src.owo.components.npc_profile import NpcProfile
from src.owo.components.relationships import Relationships
from src.owo.core.engine import SimulationEngine
from src.owo.core.work import perform_work

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "world.json"
CONTENT_DIR = REPO_ROOT / "content" / "entities"

CONFIG = {
    "quests": {"base_effort_per_hour": 5.0},
    "synergy": {"base_bonus": 1.2, "master_level_gap": 3, "apprentice_xp_bonus": 1.5},
}


def test_npc_gets_a_daily_goal_from_the_ai_provider_on_new_day():
    engine = SimulationEngine(str(CONFIG_PATH), str(CONTENT_DIR))
    birk = engine.world.get_entity_by_name("Birk")
    profile = birk.get_component(NpcProfile)

    assert profile.current_goal == ""

    for _ in range(24):  # one full day at time_speed 1.0
        engine.update(1.0)

    assert profile.current_goal == "idle"  # StubAIProvider always returns "idle"


def test_new_day_fires_once_per_day_not_per_tick():
    engine = SimulationEngine(str(CONFIG_PATH), str(CONTENT_DIR))
    calls = []
    engine.events.subscribe("new_day", lambda payload: calls.append(payload["day"]))

    for _ in range(48):
        engine.update(1.0)

    assert calls == [1, 2]


def test_coop_quest_completion_bumps_friendship_both_ways():
    from src.owo.components import quest as quest_module
    from src.owo.components import skills as skills_module
    from src.owo.core.ecs import World
    from src.owo.core.events import EventBus

    world = World()
    events = EventBus()

    a = world.create_entity("A")
    a.add_component(skills_module.Skills(levels={"woodcutting": 1}))
    a.add_component(Relationships())

    b = world.create_entity("B")
    b.add_component(skills_module.Skills(levels={"woodcutting": 1}))
    b.add_component(Relationships())

    world.create_entity("Quest").add_component(
        quest_module.Quest(skill="woodcutting", effort_required=8.0, reward_xp=10.0)
    )

    perform_work(world, CONFIG, events, "A", "Quest", dt_hours=1.0)
    perform_work(world, CONFIG, events, "B", "Quest", dt_hours=1.0)

    assert a.get_component(Relationships).friendship.get("B") == 5.0
    assert b.get_component(Relationships).friendship.get("A") == 5.0


def test_solo_quest_completion_does_not_touch_friendship():
    from src.owo.components import quest as quest_module
    from src.owo.components import skills as skills_module
    from src.owo.core.ecs import World
    from src.owo.core.events import EventBus

    world = World()
    events = EventBus()

    a = world.create_entity("A")
    a.add_component(skills_module.Skills(levels={"woodcutting": 1}))
    a.add_component(Relationships())
    world.create_entity("Quest").add_component(
        quest_module.Quest(skill="woodcutting", effort_required=1.0, reward_xp=10.0)
    )

    perform_work(world, CONFIG, events, "A", "Quest", dt_hours=1.0)

    assert a.get_component(Relationships).friendship == {}
