"""Pure progression math (no pygame, easy to unit test)."""
from settings import XP_PER_LEVEL


def level_from_xp(xp: int) -> int:
    return xp // XP_PER_LEVEL + 1


def xp_into_level(xp: int) -> tuple[int, int]:
    """Return (xp earned in current level, xp needed for the level)."""
    return xp % XP_PER_LEVEL, XP_PER_LEVEL
