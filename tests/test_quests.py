import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from game.game import Game  # noqa: E402
from game.objects import NPC  # noqa: E402
from systems.database import Database  # noqa: E402
from systems.quest_manager import QuestManager  # noqa: E402
from ui.game_scene import GameScene  # noqa: E402
from worlds.array_forest import QUESTS  # noqa: E402


class QuestManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "q.db")
        self.db.create_player("Ada")
        self.qm = QuestManager(self.db, QUESTS)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_lifecycle(self):
        got = set()
        self.assertEqual(self.qm.status("q_signs", got), "available")
        self.assertTrue(self.qm.accept("q_signs", got))
        self.assertEqual(self.qm.status("q_signs", got), "active")
        self.assertIsNone(self.qm.complete("q_signs", got))  # not ready yet
        got |= {"sign_a", "sign_b", "sign_c"}
        self.assertEqual(self.qm.status("q_signs", got), "ready")
        self.assertEqual(self.qm.complete("q_signs", got), {"xp": 40, "coins": 20})
        self.assertEqual(self.qm.status("q_signs", got), "completed")
        self.assertIsNone(self.qm.complete("q_signs", got))  # no double reward

    def test_prerequisite_and_giver_order(self):
        got = set()
        self.assertEqual(self.qm.status("q_gems", got), "locked")
        self.assertEqual(self.qm.quest_for_npc("npc_elder")["id"], "q_signs")
        self.qm.accept("q_signs", got)
        got |= {"sign_1", "sign_2", "sign_3"}
        self.qm.complete("q_signs", got)
        self.assertEqual(self.qm.status("q_gems", got), "available")
        self.assertEqual(self.qm.quest_for_npc("npc_elder")["id"], "q_gems")

    def test_earlier_progress_counts_and_persists(self):
        got = {f"coin_{i}" for i in range(1, 7)}
        self.qm.accept("q_coins", got)
        self.assertEqual(self.qm.status("q_coins", got), "ready")
        self.assertEqual(QuestManager(self.db, QUESTS).status("q_coins", got), "ready")
        self.qm.complete("q_coins", got)
        self.assertEqual(self.db.count_completed_quests(), 1)

    def test_tracker_prefers_ready(self):
        got = set()
        self.assertIsNone(self.qm.tracked(got))
        self.qm.accept("q_signs", got)
        self.qm.accept("q_chests", got)
        got |= {"chest_a", "chest_b", "chest_c"}
        self.assertEqual(self.qm.tracked(got)["id"], "q_chests")


class QuestSceneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.game = Game(Path(self.tmp.name) / "s.db")
        self.game.db.create_player("Ada")
        self.scene = GameScene(self.game, 1)

    def tearDown(self):
        self.game.shutdown()
        self.tmp.cleanup()

    def finish_dialogue(self):
        while self.scene.dialogue.active:
            self.scene.dialogue.advance()

    def npc(self, oid):
        return next(o for o in self.scene.objects if isinstance(o, NPC) and o.id == oid)

    def test_talk_accept_and_turn_in(self):
        pip = self.npc("npc_pip")
        pip.interact(self.scene)
        self.assertTrue(self.scene.dialogue.active)
        self.finish_dialogue()
        self.assertEqual(self.scene.qm.status("q_coins", self.scene.collected), "active")
        for i in range(1, 7):
            next(o for o in self.scene.objects if o.id == f"coin_{i}").collect(self.scene)
        coins_before = self.game.db.get_player()["coins"]
        pip.interact(self.scene)
        self.finish_dialogue()
        self.assertEqual(self.scene.qm.status("q_coins", self.scene.collected), "completed")
        self.assertEqual(self.game.db.get_player()["coins"], coins_before + 15)
        pip.interact(self.scene)  # now only idle chatter
        self.assertTrue(self.scene.dialogue.active)

    def test_signs_count_toward_quest(self):
        for o in self.scene.objects:
            if o.id.startswith("sign_"):
                o.interact(self.scene)
                self.finish_dialogue()
        self.assertEqual(len([c for c in self.scene.collected if c.startswith("sign_")]), 3)

    def test_draw_with_log_and_markers(self):
        self.scene.show_log = True
        self.scene.update(0.1)
        self.scene.draw(self.game.screen)
        self.scene.show_log = False
        self.scene.draw(self.game.screen)


if __name__ == "__main__":
    unittest.main()
