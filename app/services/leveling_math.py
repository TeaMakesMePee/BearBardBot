from math import sqrt

def level_exp(level: int) -> int:
    """Total EXP needed to REACH a given level from the start."""
    return 50 * (level - 1) * level

def exp_to_level(exp: int) -> int:
    return int((1 + sqrt(1 + 2 * exp / 25)) / 2)

def user_progress(exp: int) -> dict:
    level = exp_to_level(exp)
    to_level = level_exp(level + 1) - exp
    from_level = exp - level_exp(level)

    return {
        "level": level,
        "from_level": from_level,
        "to_level": to_level,
        "exp": exp,
    }


