"""Quest state machine. Pure Python (no pygame), persisted through Database.

A quest definition is a dict:
  id, giver (npc id), title, objective (text), prefix + target (count collected
  object ids that start with `prefix`), requires (quest id or None),
  xp, coins, offer / progress / complete (lists of dialogue lines).
Progress is derived from the set of collected object ids, so items picked up
before accepting a quest still count.
"""


class QuestManager:
    def __init__(self, db, defs: list[dict]):
        self.db = db
        self.defs = list(defs)
        self.by_id = {q["id"]: q for q in self.defs}
        self.states = db.get_quest_states()

    def progress(self, quest: dict, collected: set[str]) -> tuple[int, int]:
        cur = sum(1 for oid in collected if oid.startswith(quest["prefix"]))
        return min(cur, quest["target"]), quest["target"]

    def status(self, quest_id: str, collected: set[str]) -> str:
        """locked | available | active | ready | completed"""
        state = self.states.get(quest_id)
        if state == "completed":
            return "completed"
        quest = self.by_id[quest_id]
        req = quest.get("requires")
        if req and self.states.get(req) != "completed":
            return "locked"
        if state == "active":
            cur, target = self.progress(quest, collected)
            return "ready" if cur >= target else "active"
        return "available"

    def quest_for_npc(self, npc_id: str) -> dict | None:
        """The first not-yet-completed quest this NPC gives, in definition order."""
        for q in self.defs:
            if q["giver"] == npc_id and self.states.get(q["id"]) != "completed":
                return q
        return None

    def accept(self, quest_id: str, collected: set[str]) -> bool:
        if self.status(quest_id, collected) != "available":
            return False
        self._set(quest_id, "active")
        return True

    def complete(self, quest_id: str, collected: set[str]) -> dict | None:
        """Mark a ready quest completed; returns {'xp', 'coins'} to award."""
        if self.status(quest_id, collected) != "ready":
            return None
        self._set(quest_id, "completed")
        q = self.by_id[quest_id]
        return {"xp": q["xp"], "coins": q["coins"]}

    def tracked(self, collected: set[str]) -> dict | None:
        """Quest shown in the HUD: first one that is ready or active."""
        for wanted in ("ready", "active"):
            for q in self.defs:
                if self.status(q["id"], collected) == wanted:
                    return q
        return None

    def completed_count(self) -> int:
        return sum(1 for s in self.states.values() if s == "completed")

    def _set(self, quest_id: str, state: str) -> None:
        self.states[quest_id] = state
        self.db.set_quest_state(quest_id, state)
