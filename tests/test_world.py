import unittest

import pygame

from game.collision import move_and_collide
from game.world import World
from settings import TILE
from worlds.array_forest import SPAWN, build


class WorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((10, 10))
        cls.world = World(build(), SPAWN)

    def test_spawn_is_walkable(self):
        self.assertFalse(self.world.is_solid(*SPAWN))

    def test_out_of_bounds_is_solid(self):
        self.assertTrue(self.world.is_solid(-1, 5))
        self.assertTrue(self.world.is_solid(5, 999))

    def test_cannot_walk_through_tree(self):
        w = self.world
        # find a tree with a walkable tile to its left
        ty, tx = next((y, x) for y in range(2, w.h - 2) for x in range(3, w.w - 2)
                      if w.tile_at(x, y) == "T" and not w.is_solid(x - 1, y))
        pos = pygame.Vector2((tx - 1) * TILE, ty * TILE)
        new = move_and_collide(pos, (20, 14), pygame.Vector2(40, 0), w)
        self.assertLessEqual(new.x + 20, tx * TILE)

    def test_east_side_reachable_over_bridge(self):
        w, seen, stack = self.world, set(), [SPAWN]
        while stack:
            p = stack.pop()
            if p in seen or w.is_solid(*p):
                continue
            seen.add(p)
            stack += [(p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)]
        self.assertIn((56, 23), seen)   # far east end of the main road
        self.assertIn((19, 20), seen)   # in front of house 1's door


if __name__ == "__main__":
    unittest.main()
