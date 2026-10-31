import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from systems.database import Database
from systems.progression import level_from_xp, xp_into_level


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_new_save_unlocks_only_world_one(self):
        self.assertFalse(self.db.has_save())
        self.db.create_player("Ada")
        prog = self.db.get_world_progress()
        self.assertEqual([w for w, v in prog.items() if v["unlocked"]], [1])
        self.assertEqual(len(prog), 6)

    def test_new_game_overwrites(self):
        self.db.create_player("Ada")
        self.db.create_player("Bob")
        self.assertEqual(self.db.get_player()["name"], "Bob")

    def test_streak_logic(self):
        self.db.create_player("Ada")
        today = date.today()
        self.db.touch_login(today + timedelta(days=1))
        self.assertEqual(self.db.get_player()["streak"], 2)
        self.db.touch_login(today + timedelta(days=5))
        self.assertEqual(self.db.get_player()["streak"], 1)

    def test_settings_roundtrip(self):
        self.assertEqual(self.db.get_setting("x", "d"), "d")
        self.db.set_setting("x", "1")
        self.db.set_setting("x", "2")
        self.assertEqual(self.db.get_setting("x", "d"), "2")

    def test_progression(self):
        self.assertEqual(level_from_xp(0), 1)
        self.assertEqual(level_from_xp(450), 3)
        self.assertEqual(xp_into_level(450), (50, 200))


if __name__ == "__main__":
    unittest.main()
