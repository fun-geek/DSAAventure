"""Isolated execution interface.

`SandboxRunner` is the seam for a stronger backend later (Docker, Judge0, a remote
service...). `SubprocessSandbox` is the local implementation: a fresh `python -I`
process per run, empty temp working directory, minimal environment, OS resource
limits (POSIX), restricted builtins and a wall-clock timeout.

Honest note: this is layered defence for a single-player learning game, not a
hardened multi-tenant jail. Use a container/VM backend before exposing it online.
"""
import json
import os
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

from settings import SANDBOX_CASE_SECONDS, SANDBOX_MEMORY_MB

RUNNER = Path(__file__).with_name("_runner.py")


class SandboxRunner(ABC):
    @abstractmethod
    def run(self, source: str, spec: dict, cases: list[list]) -> list[dict]:
        """Run `source` on each case. Returns one outcome dict per case:
        {"status": "ok", "got": ...} | {"status": "error", "error": str} |
        {"status": "timeout"} | {"status": "skipped"}."""


class SubprocessSandbox(SandboxRunner):
    def __init__(self, case_seconds: float = SANDBOX_CASE_SECONDS,
                 memory_mb: int = SANDBOX_MEMORY_MB):
        self.case_seconds = case_seconds
        self.memory_mb = memory_mb

    def run(self, source, spec, cases):
        request = {"source": source, "spec": spec, "cases": cases,
                   "case_seconds": self.case_seconds, "memory_mb": self.memory_mb,
                   "cpu_seconds": int(self.case_seconds * 3) + 2}
        wall = self.case_seconds * 2 + 3 + 0.05 * len(cases)
        env = {"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}
        for key in ("SYSTEMROOT", "SystemRoot"):  # needed by Python on Windows
            if key in os.environ:
                env[key] = os.environ[key]
        with tempfile.TemporaryDirectory() as tmp:
            try:
                proc = subprocess.run([sys.executable, "-I", str(RUNNER)],
                                      input=json.dumps(request), capture_output=True,
                                      text=True, timeout=wall, cwd=tmp, env=env)
            except subprocess.TimeoutExpired:
                return [{"status": "timeout"}] * len(cases)
        try:
            return json.loads(proc.stdout)["results"]
        except (ValueError, KeyError):
            msg = "The program crashed or hit a memory/CPU limit."
            return [{"status": "error", "error": msg}] * len(cases)
