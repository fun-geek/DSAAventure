"""Headless end-to-end test of the menu flow (dummy video/audio drivers)."""
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from game.game import Game  # noqa: E402
from ui.main_menu import MainMenuScene, NameInputScene  # noqa: E402
from ui.game_scene import GameScene  # noqa: E402
from ui.world_select import WorldSelectScene  # noqa: E402


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode="", mod=0)


class SmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.game = Game(Path(self.tmp.name) / "s.db")

    def tearDown(self):
        self.game.shutdown()
        self.tmp.cleanup()

    def step(self, *events, n=3):
        for e in events:
            pygame.event.post(e)
        for _ in range(n):
            self.game.tick(1 / 60)

    def test_full_flow(self):
        menu = self.game.scene
        self.assertIsInstance(menu, MainMenuScene)
        self.assertFalse(menu.buttons[1].enabled)  # Continue disabled without save
        self.step(key(pygame.K_RETURN))  # New Game
        self.assertIsInstance(self.game.scene, NameInputScene)
        self.step(pygame.event.Event(pygame.TEXTINPUT, text="Ada"))
        self.step(key(pygame.K_RETURN))
        self.assertIsInstance(self.game.scene, WorldSelectScene)
        self.assertEqual(self.game.db.get_player()["name"], "Ada")
        self.step(key(pygame.K_RETURN))  # open world 1 -> exploration scene
        self.assertIsInstance(self.game.scene, GameScene)
        scene = self.game.scene
        start = scene.player.pos.copy()
        for _ in range(30):
            scene.player.update(1 / 60, pygame.Vector2(1, 0), False, scene.world)
        self.assertGreater(scene.player.pos.x, start.x)
        self.step(key(pygame.K_ESCAPE))  # pause
        self.assertTrue(scene.paused)
        self.step(key(pygame.K_DOWN), key(pygame.K_RETURN))  # Back to World Select
        self.assertIsInstance(self.game.scene, WorldSelectScene)
        self.step(key(pygame.K_ESCAPE))
        self.assertIsInstance(self.game.scene, MainMenuScene)
        self.assertTrue(self.game.scene.buttons[1].enabled)  # Continue now enabled

    def test_settings_persist(self):
        self.game.set_sfx_volume(0.3)
        self.game.set_fullscreen(False)
        self.assertEqual(self.game.db.get_setting("sfx_volume", ""), "0.30")


if __name__ == "__main__":
    unittest.main()
