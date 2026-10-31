"""Question bank + engine that grades submissions in all three modes."""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from challenges.sandbox import SandboxRunner, SubprocessSandbox
from challenges.validator import compare, static_check
from settings import CHALLENGE_MODE_MULT, REWARDS

QUESTIONS_PATH = Path(__file__).with_name("questions.json")
MODES = ("beginner", "intermediate", "advanced")


class QuestionBank:
    def __init__(self, questions: list[dict]):
        self.questions = sorted(questions, key=lambda q: (q["world"], q["order"]))
        self.by_id = {q["id"]: q for q in self.questions}

    @classmethod
    def load(cls, path: Path = QUESTIONS_PATH) -> "QuestionBank":
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f)["questions"])

    def get(self, qid: str) -> dict:
        return self.by_id[qid]

    def for_world(self, world_id: int) -> list[dict]:
        return [q for q in self.questions if q["world"] == world_id]


@dataclass
class CaseReport:
    label: str
    passed: bool
    status: str          # passed | wrong | error | timeout | skipped
    detail: str = ""


@dataclass
class RunReport:
    cases: list[CaseReport] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)  # static-check / setup problems

    @property
    def passed(self) -> int:
        return sum(c.passed for c in self.cases)

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def all_passed(self) -> bool:
        return not self.errors and self.total > 0 and self.passed == self.total


def _fmt(value) -> str:
    text = repr(value)
    return text if len(text) <= 90 else text[:87] + "..."


class ChallengeEngine:
    def __init__(self, bank: QuestionBank, sandbox: SandboxRunner | None = None):
        self.bank = bank
        self.sandbox = sandbox or SubprocessSandbox()

    @staticmethod
    def spec(q: dict) -> dict:
        return {"kind": q["kind"], "function": q["function"], "options": q.get("options", {}),
                "class_name": q.get("class_name")}

    def run(self, q: dict, source: str, include_hidden: bool = False) -> RunReport:
        """Run sample tests (and hidden tests when submitting)."""
        report = RunReport()
        report.errors = static_check(source)
        if report.errors:
            return report
        tests = [("Sample", t, False) for t in q["samples"]]
        if include_hidden:
            tests += [("Hidden", t, True) for t in q["hidden"]]
        outcomes = self.sandbox.run(source, self.spec(q), [t["args"] for _, t, _ in tests])
        counters = {"Sample": 0, "Hidden": 0}
        for (kind, test, hidden), out in zip(tests, outcomes):
            counters[kind] += 1
            label = f"{kind} test {counters[kind]}"
            status = out["status"]
            if status == "ok" and compare(q, test["args"], test["expected"], out["got"]):
                report.cases.append(CaseReport(label, True, "passed"))
                continue
            if status == "ok":
                status = "wrong"
                detail = "Wrong answer." if hidden else (
                    f"input: {self._fmt_args(q, test['args'])}\n"
                    f"expected: {_fmt(test['expected'])}\ngot: {_fmt(out['got'])}")
            elif status == "error":
                detail = out["error"]
            elif status == "timeout":
                detail = "Time limit exceeded - try a faster approach."
            else:
                detail = "Not run (an earlier test timed out)."
            report.cases.append(CaseReport(label, False, status, detail))
        return report

    @staticmethod
    def _fmt_args(q: dict, args: list) -> str:
        return ", ".join(f"{n} = {_fmt(a)}" for n, a in zip(q["arg_names"], args))

    # ---- beginner / intermediate helpers ------------------------------------
    @staticmethod
    def check_choice(q: dict, index: int) -> bool:
        return index == q["beginner"]["answer"]

    @staticmethod
    def build_fill_source(q: dict, answers: list[str]) -> tuple[str | None, list[str]]:
        """Insert the player's snippets into the template. Returns (source, errors)."""
        blanks = q["intermediate"]["blanks"]
        if len(answers) != len(blanks):
            return None, ["Wrong number of answers."]
        if any(not a.strip() for a in answers):
            return None, ["Fill in every blank first."]
        if any("\n" in a or len(a) > 120 for a in answers):
            return None, ["Each blank must be a single short line."]
        # one regex pass so an answer that happens to contain "@@2@@" is never re-substituted
        source = re.sub(r"@@(\d+)@@", lambda m: answers[int(m.group(1)) - 1].strip(), q["intermediate"]["template"])
        return source, []

    @staticmethod
    def reward(q: dict, mode: str) -> dict:
        base = REWARDS[q["difficulty"]]
        mult = CHALLENGE_MODE_MULT[mode]
        return {"xp": round(base["xp"] * mult), "coins": round(base["coins"] * mult)}
