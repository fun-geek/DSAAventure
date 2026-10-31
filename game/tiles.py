"""Procedural 16x16 jungle pixel-art tiles, scaled up to TILE size. No asset files needed."""
import random

import pygame

from settings import TILE

SOLID = set("T~ORMD")  # tree, water, rock, thatch roof, bamboo wall, door


def _surf():
    return pygame.Surface((16, 16))


def _speckle(s, base, colors, n, seed):
    rng = random.Random(seed)
    s.fill(base)
    for _ in range(n):
        s.set_at((rng.randrange(16), rng.randrange(16)), rng.choice(colors))


def _grass():
    """Dark, lush jungle floor with leaf litter."""
    s = _surf()
    _speckle(s, (36, 104, 58), [(26, 82, 46), (58, 138, 68), (84, 164, 76), (20, 66, 40)], 30, 1)
    for x, y in ((3, 5), (11, 11)):
        s.set_at((x, y), (120, 180, 70))
        s.set_at((x + 1, y), (120, 180, 70))
    return s


def _fern():
    s = _grass()
    for ang, ln in ((-60, 6), (-30, 7), (0, 7), (30, 7), (60, 6)):
        import math
        a = math.radians(ang - 90)
        for k in range(1, ln):
            x, y = 8 + int(k * math.cos(a)), 14 + int(k * math.sin(a))
            if 0 <= x < 16 and 0 <= y < 16:
                s.set_at((x, y), (86, 190, 84) if k % 2 else (48, 140, 66))
    return s


def _water(frame):
    s = _surf()
    s.fill((34, 128, 140))
    for i, y in enumerate((2, 7, 12)):
        x = (i * 5 + frame * 4) % 12
        pygame.draw.rect(s, (110, 206, 196), (x, y, 5, 1))
        pygame.draw.rect(s, (22, 100, 116), ((x + 7) % 12, y + 2, 3, 1))
    return s


def _bridge():
    """Rope-and-bamboo plank bridge."""
    s = _surf()
    s.fill((190, 158, 86))
    for x in range(0, 16, 4):
        pygame.draw.rect(s, (140, 108, 56), (x, 0, 1, 16))
    pygame.draw.rect(s, (96, 70, 36), (0, 0, 16, 2))
    pygame.draw.rect(s, (96, 70, 36), (0, 14, 16, 2))
    for x in range(1, 16, 4):  # rope lashings
        pygame.draw.rect(s, (226, 206, 150), (x, 0, 2, 2))
        pygame.draw.rect(s, (226, 206, 150), (x, 14, 2, 2))
    return s


def _path():
    """Packed red jungle clay with pebbles."""
    s = _surf()
    _speckle(s, (156, 98, 62), [(130, 78, 48), (184, 124, 80), (110, 66, 40)], 24, 2)
    for x, y in ((4, 4), (12, 9)):
        pygame.draw.rect(s, (200, 180, 150), (x, y, 2, 1))
    return s


def _flower():
    """Hibiscus, orchid and heliconia blooms."""
    s = _grass()
    pygame.draw.rect(s, (30, 100, 50), (4, 7, 1, 5))
    for (x, y), c, c2 in (((3, 4), (255, 70, 60), (255, 200, 80)), ((10, 9), (190, 90, 220), (255, 240, 250))):
        for dx, dy in ((0, 1), (1, 0), (2, 1), (1, 2)):
            s.set_at((x + dx, y + dy), c)
        s.set_at((x + 1, y + 1), c2)
    pygame.draw.polygon(s, (255, 140, 30), [(8, 13), (11, 12), (9, 15)])
    return s


def _rock():
    s = _grass()
    pygame.draw.rect(s, (96, 104, 100), (3, 6, 10, 7))
    pygame.draw.rect(s, (124, 134, 128), (4, 5, 7, 3))
    pygame.draw.rect(s, (70, 150, 70), (3, 5, 8, 2))   # moss cap
    pygame.draw.rect(s, (60, 66, 66), (3, 12, 10, 1))
    return s


def _roof():
    """Thatched palm-leaf roof."""
    s = _surf()
    s.fill((204, 168, 84))
    for y in range(0, 16, 3):
        pygame.draw.rect(s, (150, 112, 52), (0, y + 2, 16, 1))
    for x, y in ((3, 1), (9, 4), (5, 7), (12, 10), (2, 13)):
        pygame.draw.rect(s, (230, 204, 120), (x, y, 3, 1))
    return s


def _wall(door=False):
    """Bamboo wall; door is a carved wooden slab."""
    s = _surf()
    s.fill((196, 176, 104))
    for x in range(0, 16, 4):
        pygame.draw.rect(s, (150, 130, 70), (x, 0, 1, 16))
        for y in (4, 11):
            pygame.draw.rect(s, (120, 100, 50), (x, y, 4, 1))
    if door:
        pygame.draw.rect(s, (70, 44, 26), (4, 3, 8, 13))
        pygame.draw.rect(s, (112, 72, 40), (5, 4, 6, 12))
        pygame.draw.rect(s, (160, 110, 60), (7, 4, 2, 12))
        s.set_at((10, 10), (255, 220, 100))
    else:
        pygame.draw.rect(s, (30, 24, 20), (4, 4, 8, 7))
        pygame.draw.rect(s, (120, 90, 46), (4, 4, 8, 7), 1)
        pygame.draw.rect(s, (120, 90, 46), (7, 4, 2, 7))
    return s


def _tall_tree(kind: int) -> pygame.Surface:
    """16x24 jungle trees that overlap the tile above (drawn depth-sorted).
    0 = broad canopy giant, 1 = palm, 2 = flowering kapok with vines."""
    s = pygame.Surface((16, 24), pygame.SRCALPHA)
    trunk, trunk_d = (96, 64, 40), (62, 40, 28)
    if kind % 3 == 1:  # palm: curved trunk and radiating fronds
        for i, y in enumerate(range(23, 7, -1)):
            x = 8 + (1 if y < 14 else 0) + (1 if y < 10 else 0)
            pygame.draw.rect(s, trunk, (x - 1, y, 2, 1))
            if y % 3 == 0:
                pygame.draw.rect(s, trunk_d, (x - 1, y, 2, 1))
        cx, cy = 10, 8
        for ex, ey in ((0, 5), (3, 2), (7, 1), (13, 2), (15, 6), (13, 9), (1, 10)):
            pygame.draw.line(s, (30, 110, 52), (cx, cy), (ex, ey), 2)
            pygame.draw.line(s, (90, 190, 84), (cx, cy), (ex, ey - 1), 1)
        pygame.draw.circle(s, (120, 80, 40), (cx, cy + 1), 1)
    else:
        pygame.draw.rect(s, trunk, (7, 15, 3, 9))
        pygame.draw.rect(s, trunk_d, (9, 15, 1, 9))
        pygame.draw.polygon(s, trunk, [(5, 23), (7, 19), (7, 23)])
        pygame.draw.polygon(s, trunk, [(12, 23), (10, 19), (10, 23)])
        dark, mid, light = ((14, 70, 40), (28, 108, 56), (84, 176, 84)) if kind % 3 == 0 else \
                           ((16, 76, 44), (36, 122, 60), (96, 190, 90))
        for r in ((1, 5, 14, 5), (3, 2, 10, 4), (2, 9, 12, 5)):
            pygame.draw.rect(s, dark, r)
        for r in ((3, 4, 10, 4), (4, 3, 8, 2), (3, 9, 10, 3)):
            pygame.draw.rect(s, mid, r)
        for r in ((5, 4, 3, 2), (9, 8, 3, 2), (4, 10, 2, 1)):
            pygame.draw.rect(s, light, r)
        for vx in (2, 6, 13):  # hanging vines
            pygame.draw.line(s, (40, 130, 60), (vx, 12), (vx, 16 + vx % 3 * 2))
        if kind % 3 == 2:  # orange blossoms
            for x, y in ((4, 5), (10, 4), (7, 10), (12, 11), (3, 11)):
                pygame.draw.rect(s, (255, 130, 40), (x, y, 2, 2))
                s.set_at((x, y), (255, 220, 90))
    return pygame.transform.scale(s, (TILE, TILE * 3 // 2))


class TileSet:
    def __init__(self):
        def big(surface):
            return pygame.transform.scale(surface, (TILE, TILE))
        self.tiles = {".": big(_grass()), "T": big(_grass()), "=": big(_bridge()),
                      ",": big(_path()), "*": big(_flower()), "O": big(_rock()),
                      "R": big(_roof()), "M": big(_wall()), "D": big(_wall(True)),
                      "f": big(_fern())}
        self.water = [big(_water(0)), big(_water(1))]
        self.trees = [_tall_tree(k) for k in range(3)]

    def get(self, ch: str, t: float) -> pygame.Surface:
        if ch == "~":
            return self.water[int(t * 2) % 2]
        return self.tiles[ch]
