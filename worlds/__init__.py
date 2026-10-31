"""Registry of playable worlds: world id -> (layout builder, spawn, objects, quests)."""
from worlds import array_forest

WORLD_MAPS = {1: (array_forest.build, array_forest.SPAWN, array_forest.OBJECTS,
                  array_forest.QUESTS)}
