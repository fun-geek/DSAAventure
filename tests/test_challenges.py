import os
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from challenges.challenge_engine import ChallengeEngine, QuestionBank  # noqa: E402
from challenges.validator import static_check  # noqa: E402
from game.game import Game  # noqa: E402
from tools.build_questions import PROBLEMS  # noqa: E402
from ui.challenge_screen import ChallengeScene  # noqa: E402
from ui.problem_list import ProblemListScene  # noqa: E402

BANK = QuestionBank.load()
ENGINE = ChallengeEngine(BANK)
REFS = {p["id"]: p for p in PROBLEMS}
TWO_SUM_OK = ("def twoSum(nums, target):\n    seen = {}\n    for i, x in enumerate(nums):\n"
              "        if target - x in seen:\n            return [seen[target - x], i]\n        seen[x] = i\n")


class QuestionBankTests(unittest.TestCase):
    def test_curriculum_shape(self):
        counts = {w: len(BANK.for_world(w)) for w in range(1, 7)}
        self.assertEqual(counts, {1: 6, 2: 5, 3: 5, 4: 5, 5: 6, 6: 6})

    def test_every_question_is_complete(self):
        for q in BANK.questions:
            self.assertTrue(q["samples"] and q["hidden"] and q["hints"], q["id"])
            self.assertEqual(len(q["beginner"]["options"]), 4, q["id"])
            self.assertEqual(len(q["intermediate"]["blanks"]), q["intermediate"]["template"].count("@@") // 2, q["id"])
            if q["source"]["repo"]:
                self.assertTrue(q["source"]["link"].startswith("https://leetcode.com/problems/"), q["id"])
                self.assertGreater(q["source"]["companies"], 0, q["id"])

    def test_reference_solutions_pass_everything(self):
        for q in BANK.questions:
            report = ENGINE.run(q, REFS[q["id"]]["sol"], include_hidden=True)
            self.assertTrue(report.all_passed, (q["id"], [c.detail for c in report.cases if not c.passed]))

    def test_starter_code_fails(self):
        for q in BANK.questions:
            report = ENGINE.run(q, q["starter"], include_hidden=False)
            self.assertFalse(report.all_passed, q["id"])

    def test_fill_in_with_correct_answers_passes(self):
        for q in BANK.questions:
            answers = [b["answer"] for b in q["intermediate"]["blanks"]]
            source, errors = ENGINE.build_fill_source(q, answers)
            self.assertEqual(errors, [])
            self.assertTrue(ENGINE.run(q, source, include_hidden=True).all_passed, q["id"])

    def test_fill_in_rejects_blank_and_multiline(self):
        q = BANK.get("array_two_sum")
        self.assertTrue(ENGINE.build_fill_source(q, ["", "x"])[1])
        self.assertTrue(ENGINE.build_fill_source(q, ["a\nb", "x"])[1])

    def test_rewards_scale_by_mode(self):
        q = BANK.get("array_two_sum")  # easy
        self.assertEqual(ENGINE.reward(q, "advanced"), {"xp": 50, "coins": 10})
        self.assertEqual(ENGINE.reward(q, "beginner"), {"xp": 25, "coins": 5})


class SecurityTests(unittest.TestCase):
    q = BANK.get("array_two_sum")

    def run_src(self, src, hidden=False):
        return ENGINE.run(self.q, src, include_hidden=hidden)

    def test_static_blocks(self):
        for src in ("import os\n", "from subprocess import run\n", "x = open('f')\n", "eval('1')\n",
                    "x = ().__class__\n", "x = getattr(1, 'a')\n", "__import__('os')\n",
                    "import sys\n", "def f(): return type(1)\n"):
            self.assertTrue(static_check(src), src)
        self.assertEqual(static_check("import heapq\nfrom collections import deque\n"), [])

    def test_blocked_code_never_runs(self):
        self.assertTrue(self.run_src("import os\n" + TWO_SUM_OK).errors)

    def test_infinite_loop_times_out(self):
        start = time.time()
        r = self.run_src("def twoSum(nums, target):\n    while True:\n        pass\n")
        self.assertEqual(r.cases[0].status, "timeout")
        self.assertLess(time.time() - start, 8)

    def test_memory_bomb_is_contained(self):
        r = self.run_src("def twoSum(nums, target):\n    return [0] * (10 ** 11)\n")
        self.assertFalse(r.all_passed)

    def test_runtime_error_reports_line(self):
        r = self.run_src("def twoSum(nums, target):\n    return 1 / 0\n")
        self.assertIn("ZeroDivisionError", r.cases[0].detail)
        self.assertIn("line 2", r.cases[0].detail)

    def test_missing_function_message(self):
        r = self.run_src("def other():\n    pass\n")
        self.assertIn("not defined", r.cases[0].detail)

    def test_hidden_failures_do_not_leak_data(self):
        r = ENGINE.run(self.q, "def twoSum(nums, target):\n    return [0, 1]\n", include_hidden=True)
        hidden_fail = next(c for c in r.cases if c.label.startswith("Hidden") and not c.passed)
        self.assertEqual(hidden_fail.detail, "Wrong answer.")

    def test_identity_checks(self):
        r = ENGINE.run(BANK.get("ll_intersection"),
                       "def getIntersectionNode(headA, headB):\n    return headA\n", include_hidden=True)
        self.assertFalse(r.all_passed)
        c = ENGINE.run(BANK.get("graph_clone"),
                       "def cloneGraph(node):\n    return node\n", include_hidden=True)
        self.assertFalse(c.all_passed)


class ChallengeSceneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.game = Game(Path(self.tmp.name) / "c.db")
        self.game.db.create_player("Ada")
        self.q = BANK.get("array_two_sum")

    def tearDown(self):
        self.game.shutdown()
        self.tmp.cleanup()

    def wait(self, scene):
        for _ in range(400):
            scene.update(0.02)
            if not scene.running:
                return
            time.sleep(0.02)
        self.fail("grader never finished")

    def test_beginner_correct_and_wrong(self):
        scene = ChallengeScene(self.game, self.q)
        scene.choice = (self.q["beginner"]["answer"] + 1) % 4
        scene._run(True)
        self.assertEqual(self.game.db.get_player()["xp"], 0)
        scene.choice = self.q["beginner"]["answer"]
        scene._run(True)
        player = self.game.db.get_player()
        self.assertEqual((player["xp"], player["coins"]), (25, 5))
        scene._run(True)  # solving again pays nothing
        self.assertEqual(self.game.db.get_player()["xp"], 25)
        scene.draw(self.game.screen)

    def test_advanced_submit_awards_once(self):
        scene = ChallengeScene(self.game, self.q)
        scene._set_mode("advanced")
        scene.editor.set_text(TWO_SUM_OK)
        scene._run(False)
        self.wait(scene)
        self.assertTrue(scene.report.all_passed)
        self.assertEqual(self.game.db.get_player()["xp"], 0)  # a plain run never pays
        scene._run(True)
        self.wait(scene)
        self.assertEqual(self.game.db.get_player()["xp"], 50)
        scene.draw(self.game.screen)
        self.assertIn("array_two_sum", self.game.db.solved_questions())

    def test_intermediate_flow_and_failed_attempt(self):
        scene = ChallengeScene(self.game, self.q)
        scene._set_mode("intermediate")
        scene._run(True)  # blanks empty
        self.assertTrue(scene.report.errors)
        for f, b in zip(scene.fields, self.q["intermediate"]["blanks"]):
            f.text = b["answer"]
        scene._run(True)
        self.wait(scene)
        self.assertEqual(self.game.db.get_player()["xp"], 38)  # 75% of 50, rounded
        scene.draw(self.game.screen)

    def test_wrong_code_records_attempt_only(self):
        scene = ChallengeScene(self.game, self.q)
        scene._set_mode("advanced")
        scene._run(True)  # starter code fails
        self.wait(scene)
        self.assertFalse(scene.report.all_passed)
        self.assertEqual(self.game.db.get_challenge_progress()["array_two_sum"]["advanced"], False)
        self.assertEqual(self.game.db.get_player()["xp"], 0)

    def test_every_question_screen_draws_in_every_mode(self):
        for q in BANK.questions:
            scene = ChallengeScene(self.game, q)
            for mode in ("beginner", "intermediate", "advanced"):
                scene._set_mode(mode)
                scene.draw(self.game.screen)
            pygame.key.stop_text_input()

    def test_editor_typing_and_autoindent(self):
        scene = ChallengeScene(self.game, self.q)
        ed = scene.editor
        ed.set_text("")
        for text in ("def f(x):", "\n", "return x"):
            ed.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=text))
        self.assertEqual(ed.text, "def f(x):\n    return x")

    def test_problem_list_and_practice(self):
        lst = ProblemListScene(self.game, 3)
        self.game.push(lst)
        lst.draw(self.game.screen)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="", mod=0))
        self.game.tick(0.02)
        self.assertIsInstance(self.game.scene, ChallengeScene)
        self.assertEqual(self.game.scene.q["world"], 3)


if __name__ == "__main__":
    unittest.main()
