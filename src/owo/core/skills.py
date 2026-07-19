from src.owo.components.skills import Skills

XP_PER_LEVEL = 100.0


def skill_level(skills: Skills, skill_name: str) -> int:
    return skills.levels.get(skill_name, 1)


def skill_efficiency(level: int) -> float:
    """Higher level = more effort produced per hour worked. Used to reduce
    time (and, via the caller, energy) spent per unit of quest progress."""
    return 1.0 + 0.15 * (level - 1)


def add_xp(skills: Skills, skill_name: str, amount: float) -> bool:
    """Adds xp for a skill, leveling it up if a threshold is crossed.
    Returns True if a level-up happened."""
    if amount <= 0:
        return False

    skills.xp[skill_name] = skills.xp.get(skill_name, 0.0) + amount
    current_level = skills.levels.get(skill_name, 1)
    new_level = int(skills.xp[skill_name] // XP_PER_LEVEL) + 1

    if new_level > current_level:
        skills.levels[skill_name] = new_level
        return True
    return False
