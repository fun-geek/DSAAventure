"""Environment objects: chests, pickups, signs, campfire (procedural sprites)."""
import math

import pygame

from game.player import _frame
from settings import CHEST_REWARD, PICKUP_REWARDS, TILE


def _px(w=16, h=16):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def _up(s):
    return pygame.transform.scale(s, (s.get_width() * 2, s.get_height() * 2))


_CACHE: dict = {}


def sprites() -> dict:
    """Build every object sprite once (needs no display)."""
    if _CACHE:
        return _CACHE
    wood, wood_l, gold, dark = (140, 90, 48), (172, 112, 60), (240, 200, 70), (70, 44, 26)
    for opened in (False, True):
        s = _px()
        pygame.draw.rect(s, dark, (1, 6, 14, 10))
        pygame.draw.rect(s, wood, (2, 7, 12, 8))
        if opened:
            pygame.draw.rect(s, dark, (1, 1, 14, 5))
            pygame.draw.rect(s, wood_l, (2, 2, 12, 3))
            pygame.draw.rect(s, (255, 226, 120), (3, 7, 10, 2))
        else:
            pygame.draw.rect(s, dark, (1, 3, 14, 5))
            pygame.draw.rect(s, wood_l, (2, 4, 12, 3))
            pygame.draw.rect(s, (90, 60, 30), (7, 8, 2, 2))
        pygame.draw.rect(s, gold, (7, 3 if not opened else 1, 2, 12 if not opened else 14))
        _CACHE["chest_open" if opened else "chest"] = _up(s)
    s = _px()
    pygame.draw.rect(s, (110, 74, 44), (7, 8, 2, 8))
    pygame.draw.rect(s, dark, (1, 1, 14, 8))
    pygame.draw.rect(s, (206, 166, 104), (2, 2, 12, 6))
    pygame.draw.rect(s, dark, (4, 4, 8, 1))
    pygame.draw.rect(s, dark, (4, 6, 5, 1))
    _CACHE["sign"] = _up(s)
    _CACHE["coin"] = []
    for w in (8, 5, 2, 5):
        s = _px()
        pygame.draw.ellipse(s, (200, 150, 30), (8 - w // 2, 4, w, 9))
        pygame.draw.ellipse(s, gold, (8 - w // 2, 3, w, 8))
        _CACHE["coin"].append(_up(s))
    s = _px()
    pygame.draw.polygon(s, (60, 130, 220), [(8, 2), (13, 7), (8, 14), (3, 7)])
    pygame.draw.polygon(s, (140, 200, 255), [(8, 2), (3, 7), (8, 7)])
    pygame.draw.polygon(s, (30, 80, 170), [(8, 7), (13, 7), (8, 14)])
    _CACHE["gem"] = [_up(s)]
    for solved in (False, True):  # carved jungle totem: glowing eyes + rune
        s = _px()
        glow = (90, 230, 120) if solved else (255, 190, 60)
        pygame.draw.rect(s, (50, 56, 54), (4, 1, 8, 14))
        pygame.draw.rect(s, (92, 102, 96), (5, 1, 6, 13))
        pygame.draw.rect(s, (60, 130, 66), (4, 1, 8, 2))        # moss
        pygame.draw.rect(s, (60, 130, 66), (4, 12, 3, 3))
        pygame.draw.rect(s, (30, 34, 32), (3, 14, 10, 2))
        pygame.draw.rect(s, (24, 28, 26), (6, 4, 4, 1))         # brow
        s.set_at((6, 5), glow)
        s.set_at((9, 5), glow)
        pygame.draw.rect(s, glow, (7, 8, 2, 4))                  # rune
        pygame.draw.rect(s, glow, (6, 9, 4, 1))
        _CACHE["totem_solved" if solved else "totem"] = _up(s)
    _CACHE["fire"] = []
    for f in range(3):
        s = _px()
        pygame.draw.rect(s, (110, 112, 120), (2, 13, 12, 2))
        pygame.draw.rect(s, (90, 58, 36), (3, 11, 10, 2))
        pygame.draw.polygon(s, (230, 100, 36), [(4, 12), (8, 3 + f), (12, 12)])
        pygame.draw.polygon(s, (255, 200, 70), [(6, 12), (8, 6 + f), (10, 12)])
        _CACHE["fire"].append(_up(s))
    return _CACHE


class GameObject:
    solid = False
    interactive = False
    persistent = False

    def __init__(self, oid: str, tx: int, ty: int):
        self.id, self.tx, self.ty = oid, tx, ty
        self.rect = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
        self.done = False

    @property
    def sort_y(self) -> int:
        return self.rect.bottom

    prompt = ""

    def restore(self) -> None:
        """Re-apply saved state when a collected/opened object is loaded."""
        self.done = True

    def draw_item(self, t: float):
        raise NotImplementedError

    def interact(self, scene) -> None:
        pass


class Chest(GameObject):
    solid, interactive, persistent = True, True, True
    prompt = "E  Open chest"

    def draw_item(self, t):
        return sprites()["chest_open" if self.done else "chest"], self.rect.topleft

    def interact(self, scene) -> None:
        if self.done:
            return
        self.done = True
        scene.mark(self)
        scene.play("chest")
        scene.grant(CHEST_REWARD["coins"], CHEST_REWARD["xp"], self.rect.center)


class Pickup(GameObject):
    persistent = True

    def __init__(self, oid, tx, ty, kind="coin"):
        super().__init__(oid, tx, ty)
        self.kind = kind

    @property
    def sort_y(self) -> int:
        return self.rect.top  # always drawn beneath the player

    def draw_item(self, t):
        frames = sprites()[self.kind]
        img = frames[int(t * 8 + self.tx) % len(frames)]
        bob = round(math.sin(t * 3 + self.tx) * 3)
        return img, (self.rect.x, self.rect.y + bob - 4)

    def collect(self, scene) -> None:
        if self.done:
            return
        self.done = True
        scene.mark(self)
        scene.play("coin")
        r = PICKUP_REWARDS[self.kind]
        scene.grant(r["coins"], r["xp"], self.rect.center, quiet_sound=True)


class Sign(GameObject):
    solid, interactive = True, True
    prompt = "E  Read sign"

    def __init__(self, oid, tx, ty, text):
        super().__init__(oid, tx, ty)
        self.text = text
        self.done = False

    def restore(self) -> None:
        pass

    def draw_item(self, t):
        return sprites()["sign"], self.rect.topleft

    def interact(self, scene) -> None:
        scene.mark(self)  # remember that this sign was read (quest progress)
        scene.say("Signpost", self.text)


class Totem(GameObject):
    """A carved totem: each one opens a coding puzzle (Phase 5)."""
    solid, interactive = True, True
    prompt = "E  Solve puzzle"

    def __init__(self, oid, tx, ty, qid):
        super().__init__(oid, tx, ty)
        self.qid = qid
        self.solved = False

    def restore(self) -> None:
        pass

    @property
    def done(self) -> bool:  # never hides the prompt
        return False

    @done.setter
    def done(self, value) -> None:
        pass

    def draw_item(self, t):
        img = sprites()["totem_solved" if self.solved else "totem"]
        glow = int(2 + 1.5 * math.sin(t * 3 + self.tx))
        return img, (self.rect.x, self.rect.y - glow // 2)

    def interact(self, scene) -> None:
        scene.open_challenge(self.qid)


class Campfire(GameObject):
    solid = True

    def draw_item(self, t):
        frames = sprites()["fire"]
        return frames[int(t * 6) % len(frames)], self.rect.topleft

    def restore(self) -> None:
        pass


LOOKS = {
    "elder": {"hair": (235, 235, 240), "tunic": (150, 60, 50), "dark": (100, 36, 34),
              "trousers": (70, 50, 40), "hat": (230, 70, 60), "hat_dark": (255, 210, 80)},
    "merchant": {"hair": (60, 40, 30), "tunic": (232, 190, 70), "dark": (170, 120, 30),
                 "trousers": (90, 60, 40), "hat": (236, 210, 130), "hat_dark": (176, 140, 70)},
    "ranger": {"hair": (170, 70, 40), "tunic": (46, 120, 84), "dark": (28, 80, 56),
               "trousers": (60, 70, 60), "hat": (40, 90, 60), "hat_dark": (24, 60, 40)},
}


class NPC(GameObject):
    """A villager. Dialogue and quests are driven by the scene's QuestManager."""
    solid, interactive = True, True
    prompt = "E  Talk"

    def __init__(self, oid, tx, ty, name, look, idle):
        super().__init__(oid, tx, ty)
        self.name, self.idle, self.idle_i = name, idle, 0
        self.facing = "down"
        self.frames = {d: _frame(d, 0, LOOKS[look]) for d in ("down", "up", "left", "right")}

    def restore(self) -> None:
        pass

    def face_towards(self, point) -> None:
        dx, dy = point[0] - self.rect.centerx, point[1] - self.rect.centery
        if abs(dx) > abs(dy):
            self.facing = "right" if dx > 0 else "left"
        else:
            self.facing = "down" if dy > 0 else "up"

    def next_idle(self) -> str:
        line = self.idle[self.idle_i % len(self.idle)]
        self.idle_i += 1
        return line

    def draw_item(self, t):
        bob = round(math.sin(t * 2 + self.tx) * 1)
        return self.frames[self.facing], (self.rect.x, self.rect.y + bob)

    def interact(self, scene) -> None:
        scene.talk_to(self)


def make_object(d: dict) -> GameObject:
    kind = d["kind"]
    if kind == "chest":
        return Chest(d["id"], d["tx"], d["ty"])
    if kind in PICKUP_REWARDS:
        return Pickup(d["id"], d["tx"], d["ty"], kind)
    if kind == "sign":
        return Sign(d["id"], d["tx"], d["ty"], d["text"])
    if kind == "npc":
        return NPC(d["id"], d["tx"], d["ty"], d["name"], d["look"], d["idle"])
    if kind == "totem":
        return Totem(d["id"], d["tx"], d["ty"], d["qid"])
    if kind == "campfire":
        return Campfire(d["id"], d["tx"], d["ty"])
    raise ValueError(f"Unknown object kind: {kind}")
