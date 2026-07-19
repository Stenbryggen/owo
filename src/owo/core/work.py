from src.owo.components.quest import Quest
from src.owo.components.skills import Skills
from src.owo.components.wallet import Wallet
from src.owo.core.skills import add_xp, skill_efficiency, skill_level


def quest_progress(quest: Quest) -> float:
    return sum(quest.contributors.values())


def quest_is_complete(quest: Quest) -> bool:
    return quest_progress(quest) >= quest.effort_required


def perform_work(world, config, events, actor_name: str, quest_name: str, dt_hours: float) -> None:
    """One entity spends dt_hours working on one quest. Called on demand
    (e.g. from player input or NPC behavior), not as a per-tick System -
    quest work only happens when someone is actually doing it."""
    if dt_hours <= 0:
        return

    actor = world.get_entity_by_name(actor_name)
    quest_entity = world.get_entity_by_name(quest_name)
    if actor is None or quest_entity is None:
        return

    quest = quest_entity.get_component(Quest)
    skills = actor.get_component(Skills)
    if quest is None or skills is None or quest.status == "completed":
        return

    level = skill_level(skills, quest.skill)
    base_effort = config["quests"]["base_effort_per_hour"] * skill_efficiency(level) * dt_hours

    other_contributors = [name for name in quest.contributors if name != actor_name]
    synergy_bonus = config["synergy"]["base_bonus"] if other_contributors else 1.0
    effort = base_effort * synergy_bonus

    remaining = max(0.0, quest.effort_required - quest_progress(quest))
    effort = min(effort, remaining)
    quest.contributors[actor_name] = quest.contributors.get(actor_name, 0.0) + effort
    quest.status = "in_progress"

    events.publish(
        "quest_progress",
        {"quest": quest_name, "by": actor_name, "effort": effort, "synergy": synergy_bonus > 1.0},
    )

    if quest_is_complete(quest):
        _complete_quest(world, config, events, quest_name, quest)


def _complete_quest(world, config, events, quest_name: str, quest: Quest) -> None:
    quest.status = "completed"
    master_gap = config["synergy"]["master_level_gap"]
    apprentice_bonus = config["synergy"]["apprentice_xp_bonus"]
    total_effort = quest_progress(quest) or 1.0

    contributor_levels = {}
    for name in quest.contributors:
        entity = world.get_entity_by_name(name)
        skills = entity.get_component(Skills) if entity else None
        contributor_levels[name] = skill_level(skills, quest.skill) if skills else 1

    for name, contributed in quest.contributors.items():
        entity = world.get_entity_by_name(name)
        if entity is None:
            continue

        share = contributed / total_effort
        xp_awarded = quest.reward_xp * share
        gold_awarded = quest.reward_gold * share

        is_apprentice = any(
            other_level - contributor_levels[name] >= master_gap
            for other_name, other_level in contributor_levels.items()
            if other_name != name
        )
        if is_apprentice:
            xp_awarded *= apprentice_bonus

        skills = entity.get_component(Skills)
        if skills is not None:
            leveled_up = add_xp(skills, quest.skill, xp_awarded)
            events.publish(
                "xp_gained", {"entity": name, "skill": quest.skill, "amount": xp_awarded}
            )
            if leveled_up:
                events.publish(
                    "leveled_up",
                    {"entity": name, "skill": quest.skill, "level": skills.levels[quest.skill]},
                )

        wallet = entity.get_component(Wallet)
        if wallet is not None and gold_awarded:
            wallet.gold += gold_awarded

    events.publish("quest_completed", {"quest": quest_name, "contributors": list(quest.contributors)})
