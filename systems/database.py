"""SQLite persistence for player progress and user settings."""
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from settings import WORLDS

SCHEMA = """
CREATE TABLE IF NOT EXISTS player (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL,
    xp INTEGER NOT NULL DEFAULT 0,
    coins INTEGER NOT NULL DEFAULT 0,
    streak INTEGER NOT NULL DEFAULT 0,
    last_played TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS world_progress (
    world_id INTEGER PRIMARY KEY,
    unlocked INTEGER NOT NULL DEFAULT 0,
    completed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS collected (
    world_id INTEGER NOT NULL,
    obj_id TEXT NOT NULL,
    PRIMARY KEY (world_id, obj_id)
);
CREATE TABLE IF NOT EXISTS quests (
    quest_id TEXT PRIMARY KEY,
    state TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS challenge_progress (
    question_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    solved INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (question_id, mode)
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class Database:
    """Thin wrapper over sqlite3. One save slot (player id = 1)."""

    def __init__(self, path: Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        with self.conn:
            self.conn.executescript(SCHEMA)

    # ---- player ----------------------------------------------------------
    def has_save(self) -> bool:
        return self.conn.execute("SELECT 1 FROM player WHERE id = 1").fetchone() is not None

    def create_player(self, name: str) -> None:
        """Start a fresh save, replacing any existing one."""
        today = date.today().isoformat()
        with self.conn:
            self.conn.execute("DELETE FROM player")
            self.conn.execute("DELETE FROM world_progress")
            self.conn.execute("DELETE FROM collected")
            self.conn.execute("DELETE FROM quests")
            self.conn.execute("DELETE FROM challenge_progress")
            self.conn.execute(
                "INSERT INTO player (id, name, streak, last_played, created_at)"
                " VALUES (1, ?, 1, ?, ?)", (name.strip(), today, today))
            for w in WORLDS:
                self.conn.execute(
                    "INSERT INTO world_progress (world_id, unlocked) VALUES (?, ?)",
                    (w["id"], 1 if w["id"] == 1 else 0))

    def get_player(self) -> dict | None:
        row = self.conn.execute("SELECT * FROM player WHERE id = 1").fetchone()
        return dict(row) if row else None

    def touch_login(self, today: date | None = None) -> None:
        """Update the daily streak: +1 if last played yesterday, reset if later."""
        player = self.get_player()
        if not player:
            return
        today = today or date.today()
        last = player["last_played"]
        if last == today.isoformat():
            return
        streak = player["streak"] + 1 if last == (today - timedelta(days=1)).isoformat() else 1
        with self.conn:
            self.conn.execute("UPDATE player SET streak = ?, last_played = ? WHERE id = 1",
                              (streak, today.isoformat()))

    def add_rewards(self, coins: int = 0, xp: int = 0) -> None:
        with self.conn:
            self.conn.execute("UPDATE player SET coins = coins + ?, xp = xp + ? WHERE id = 1",
                              (coins, xp))

    def mark_collected(self, world_id: int, obj_id: str) -> None:
        with self.conn:
            self.conn.execute("INSERT OR IGNORE INTO collected VALUES (?, ?)", (world_id, obj_id))

    def get_collected(self, world_id: int) -> set[str]:
        rows = self.conn.execute("SELECT obj_id FROM collected WHERE world_id = ?",
                                 (world_id,)).fetchall()
        return {r["obj_id"] for r in rows}

    def get_quest_states(self) -> dict[str, str]:
        return {r["quest_id"]: r["state"]
                for r in self.conn.execute("SELECT quest_id, state FROM quests")}

    def set_quest_state(self, quest_id: str, state: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO quests (quest_id, state) VALUES (?, ?)"
                " ON CONFLICT(quest_id) DO UPDATE SET state = excluded.state", (quest_id, state))

    def count_completed_quests(self) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM quests WHERE state = 'completed'").fetchone()[0]

    def record_challenge_result(self, question_id: str, mode: str, solved: bool) -> bool:
        """Store an attempt. Returns True only on the first solve of (question, mode)."""
        with self.conn:
            row = self.conn.execute(
                "SELECT solved FROM challenge_progress WHERE question_id = ? AND mode = ?",
                (question_id, mode)).fetchone()
            first = solved and not (row and row["solved"])
            self.conn.execute(
                "INSERT INTO challenge_progress (question_id, mode, attempts, solved)"
                " VALUES (?, ?, 1, ?) ON CONFLICT(question_id, mode) DO UPDATE SET"
                " attempts = attempts + 1, solved = MAX(solved, excluded.solved)",
                (question_id, mode, int(solved)))
        return first

    def get_challenge_progress(self) -> dict[str, dict[str, bool]]:
        out: dict[str, dict[str, bool]] = {}
        for r in self.conn.execute("SELECT * FROM challenge_progress"):
            out.setdefault(r["question_id"], {})[r["mode"]] = bool(r["solved"])
        return out

    def solved_questions(self) -> set[str]:
        return {r["question_id"] for r in self.conn.execute(
            "SELECT DISTINCT question_id FROM challenge_progress WHERE solved = 1")}

    # ---- worlds ----------------------------------------------------------
    def get_world_progress(self) -> dict[int, dict]:
        rows = self.conn.execute("SELECT * FROM world_progress").fetchall()
        return {r["world_id"]: {"unlocked": bool(r["unlocked"]),
                                "completed": bool(r["completed"])} for r in rows}

    # ---- settings --------------------------------------------------------
    def get_setting(self, key: str, default: str) -> str:
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))

    def close(self) -> None:
        self.conn.close()
