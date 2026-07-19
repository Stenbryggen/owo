from src.owo.components import quest as quest_module
from src.owo.components import skills as skills_module
from src.owo.components import wallet as wallet_module
from src.owo.core.ecs import World
from src.owo.core.events import EventBus
from src.owo.core.work import perform_work, quest_progress

CONFIG = {
    "quests": {"base_effort_per_hour": 5.0},
    "synergy": {"base_bonus": 1.2, "master_level_gap": 3, "apprentice_xp_bonus": 1.5},
}


def _make_worker(world, name, level=1, skill="woodcutting"):
    entity = world.create_entity(name)
    entity.add_component(skills_module.Skills(levels={skill: level}, xp={skill: 0.0}))
    entity.add_component(wallet_module.Wallet(gold=0.0))
    return entity


def _make_quest(world, name="Quest", skill="woodcutting", effort_required=10.0,
                 reward_gold=0.0, reward_xp=100.0):
    entity = world.create_entity(name)
    entity.add_component(
        quest_module.Quest(
            skill=skill, effort_required=effort_required,
            reward_gold=reward_gold, reward_xp=reward_xp,
        )
    )
    return entity


def test_solo_work_progresses_quest_without_synergy():
    world = World()
    events = EventBus()
    _make_worker(world, "Solo")
    quest_entity = _make_quest(world, effort_required=100.0)

    perform_work(world, CONFIG, events, "Solo", "Quest", dt_hours=1.0)

    quest = quest_entity.get_component(quest_module.Quest)
    assert quest.status == "in_progress"
    assert quest_progress(quest) == 5.0  # base_effort_per_hour, no synergy, level-1 efficiency


def test_second_contributor_gets_synergy_bonus():
    world = World()
    events = EventBus()
    _make_worker(world, "A")
    _make_worker(world, "B")
    quest_entity = _make_quest(world, effort_required=100.0)

    perform_work(world, CONFIG, events, "A", "Quest", dt_hours=1.0)
    progress_before_b = quest_progress(quest_entity.get_component(quest_module.Quest))

    perform_work(world, CONFIG, events, "B", "Quest", dt_hours=1.0)
    quest = quest_entity.get_component(quest_module.Quest)

    b_contribution = quest.contributors["B"]
    assert b_contribution == 5.0 * 1.2  # synergy bonus applied since A already contributed
    assert quest_progress(quest) == progress_before_b + b_contribution


def test_quest_completion_pays_gold_and_xp_proportional_to_contribution():
    world = World()
    events = EventBus()
    _make_worker(world, "Solo")
    quest_entity = _make_quest(world, effort_required=5.0, reward_gold=50.0, reward_xp=100.0)

    perform_work(world, CONFIG, events, "Solo", "Quest", dt_hours=1.0)

    quest = quest_entity.get_component(quest_module.Quest)
    assert quest.status == "completed"

    solo = world.get_entity_by_name("Solo")
    assert solo.get_component(wallet_module.Wallet).gold == 50.0
    assert solo.get_component(skills_module.Skills).xp["woodcutting"] == 100.0


def test_apprentice_gets_xp_bonus_when_working_with_a_master():
    world = World()
    events = EventBus()
    _make_worker(world, "Apprentice", level=1)
    _make_worker(world, "Master", level=5)
    quest_entity = _make_quest(world, effort_required=10.0, reward_xp=100.0)

    # Master contributes first so the apprentice's later call sees a co-op quest.
    perform_work(world, CONFIG, events, "Master", "Quest", dt_hours=1.0)
    perform_work(world, CONFIG, events, "Apprentice", "Quest", dt_hours=10.0)

    quest = quest_entity.get_component(quest_module.Quest)
    assert quest.status == "completed"

    apprentice = world.get_entity_by_name("Apprentice")
    apprentice_share = quest.contributors["Apprentice"] / quest_progress(quest)
    expected_base_xp = 100.0 * apprentice_share
    actual_xp = apprentice.get_component(skills_module.Skills).xp["woodcutting"]

    assert actual_xp > expected_base_xp  # apprentice bonus multiplier was applied


def test_leveled_up_event_fires_when_xp_crosses_threshold():
    world = World()
    events = EventBus()
    levels = []
    events.subscribe("leveled_up", lambda payload: levels.append(payload))

    _make_worker(world, "Solo")
    _make_quest(world, effort_required=1.0, reward_xp=150.0)

    perform_work(world, CONFIG, events, "Solo", "Quest", dt_hours=1.0)

    assert levels == [{"entity": "Solo", "skill": "woodcutting", "level": 2}]
