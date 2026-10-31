import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from game.game import Game  # noqa: E402
from game.objects import Chest, Pickup, Sign  # noqa: E402
from settings import CHEST_REWARD, PICKUP_REWARDS  # noqa: E402
from ui.game_scene import GameScene  # noqa: E402


class ObjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.game = Game(Path(self.tmp.name) / "o.db")
        self.game.db.create_player("Ada")
        self.scene = GameScene(self.game, 1)

    def tearDown(self):
        self.game.shutdown()
        self.tmp.cleanup()

    def obj(self, cls, oid=None):
        return next(o for o in self.scene.objects if isinstance(o, cls) and (oid is None or o.id == oid))

    def test_chest_rewards_once_and_persists(self):
        chest = self.obj(Chest)
        chest.interact(self.scene)
        chest.interact(self.scene)  # second open does nothing
        p = self.game.db.get_player()
        self.assertEqual((p["coins"], p["xp"]), (CHEST_REWARD["coins"], CHEST_REWARD["xp"]))
        reloaded = GameScene(self.game, 1)
        self.assertTrue(next(o for o in reloaded.objects if o.id == chest.id).done)

    def test_gem_collect_and_level_up(self):
        gem = self.obj(Pickup, "gem_1")
        gem.collect(self.scene)
        self.assertEqual(self.game.db.get_player()["coins"], PICKUP_REWARDS["gem"]["coins"])
        self.scene.grant(0, 300, (0, 0))
        self.assertTrue(any(f[0] == "LEVEL UP!" for f in self.scene.floaters))

    def test_sign_opens_dialogue(self):
        self.obj(Sign).interact(self.scene)
        self.assertTrue(self.scene.dialogue.active)
        self.scene.dialogue.advance()  # finish typing
        self.scene.dialogue.advance()  # close
        self.assertFalse(self.scene.dialogue.active)

    def test_new_game_resets_collected(self):
        self.obj(Chest).interact(self.scene)
        self.game.db.create_player("Bob")
        self.assertEqual(self.game.db.get_collected(1), set())

    def test_all_objects_reachable(self):
        w = self.scene.world
        seen, stack = set(), [w.spawn]
        while stack:
            p = stack.pop()
            if p in seen or w.is_solid(*p):
                continue
            seen.add(p)
            stack += [(p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)]
        for o in self.scene.objects:
            if o.solid:
                near = [(o.tx + dx, o.ty + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                self.assertTrue(any(n in seen for n in near), o.id)
            else:
                self.assertIn((o.tx, o.ty), seen, o.id)

    def test_draw_runs(self):
        self.scene.draw(self.game.screen)
        self.scene.say("Test", "Hello adventurer, this is a long enough line to wrap across rows.")
        self.scene.update(0.5)
        self.scene.draw(self.game.screen)


if __name__ == "__main__":
    unittest.main()
