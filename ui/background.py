"""Procedurally generated, animated pixel-art jungle (no image assets needed)."""
import math
import random

import pygame

from settings import PIXEL_H, PIXEL_W, SCREEN_H, SCREEN_W


class JungleBackground:
    """Golden-hour jungle: tepui with a waterfall, giant trunks, hanging vines,
    sun shafts, drifting mist, fireflies and a macaw flying across."""

    def __init__(self, seed: int = 11):
        rng = random.Random(seed)
        w, h = PIXEL_W, PIXEL_H
        self.static = pygame.Surface((w, h))
        self.work = pygame.Surface((w, h))
        self.beams = pygame.Surface((w, h), pygame.SRCALPHA)

        # Sky: teal at the top melting into amber near the horizon
        bands = [(8, 36, 48), (14, 62, 66), (28, 102, 88), (86, 148, 96), (196, 176, 90), (250, 168, 78)]
        sky_h = 104
        for i, c in enumerate(bands):
            self.static.fill(c, (0, i * sky_h // len(bands), w, sky_h // len(bands) + 1))
        pygame.draw.circle(self.static, (255, 214, 120), (150, 74), 20)   # sun halo
        pygame.draw.circle(self.static, (255, 236, 160), (150, 74), 12)

        # Distant table mountains (tepui) with a waterfall
        for cx, top, half in ((60, 54, 34), (176, 46, 40)):
            for x in range(cx - half, cx + half):
                edge = min(x - (cx - half), (cx + half) - x)
                y0 = top + max(0, 8 - edge) * 2
                pygame.draw.line(self.static, (26, 84, 78), (x, y0), (x, 112))
            pygame.draw.line(self.static, (40, 110, 94), (cx - half + 3, top + 1), (cx + half - 3, top + 1))
        self.fall_x, self.fall_top = 176, 52
        pygame.draw.rect(self.static, (150, 210, 200), (self.fall_x - 1, self.fall_top, 3, 60))

        # Layers of rounded tree crowns for depth
        for base, col, count, rad in ((104, (24, 82, 60), 22, (9, 15)), (116, (18, 66, 46), 20, (10, 17))):
            for i in range(count):
                x, r = int(i * w / count + rng.randint(-4, 4)), rng.randint(*rad)
                pygame.draw.circle(self.static, col, (x, base - rng.randint(0, 6)), r)
            self.static.fill(col, (0, base, w, 40))

        # Jungle floor with ferns
        self.static.fill((20, 54, 36), (0, 128, w, h - 128))
        for _ in range(240):
            self.static.set_at((rng.randrange(w), rng.randrange(128, h)),
                               rng.choice([(34, 96, 52), (14, 40, 28), (60, 130, 64)]))
        for _ in range(20):
            self._fern(self.static, rng.randrange(w), rng.randrange(130, 156), rng)
        pygame.draw.rect(self.static, (110, 74, 44), (0, 146, w, 5))     # trail
        pygame.draw.rect(self.static, (84, 56, 34), (0, 150, w, 1))

        # Giant trunks with buttress roots and vines
        for x in (18, 70, 128, 196, 232):
            tw = rng.randint(8, 12)
            pygame.draw.rect(self.static, (58, 38, 26), (x - tw // 2, 0, tw, 146))
            pygame.draw.rect(self.static, (84, 56, 36), (x - tw // 2, 0, 3, 146))
            pygame.draw.polygon(self.static, (58, 38, 26), [(x - tw // 2 - 8, 148), (x - tw // 2, 128), (x - tw // 2, 148)])
            pygame.draw.polygon(self.static, (58, 38, 26), [(x + tw // 2 + 8, 148), (x + tw // 2, 128), (x + tw // 2, 148)])
            for _ in range(5):
                self.static.fill((52, 120, 60), (x - tw // 2 + rng.randint(0, tw - 2), rng.randint(20, 120), 2, 2))
        # Canopy ceiling with hanging vines
        for x in range(-6, w + 8, 7):
            pygame.draw.circle(self.static, rng.choice([(10, 46, 30), (16, 62, 38), (22, 80, 44)]),
                               (x, rng.randint(-2, 8)), rng.randint(8, 13))
        for _ in range(26):
            vx, vl = rng.randrange(w), rng.randint(14, 70)
            pygame.draw.line(self.static, (30, 100, 48), (vx, 6), (vx + rng.randint(-2, 2), 6 + vl))
            for k in range(3, vl, 9):
                self.static.fill((70, 160, 70), (vx + (k // 9) % 2 * 2 - 1, 6 + k, 3, 2))
        # Foreground leaves in the corners
        for sign, x0 in ((1, 0), (-1, w)):
            for k in range(6):
                ang = math.radians(rng.randint(8, 60))
                ln = rng.randint(30, 60)
                tip = (x0 + sign * int(ln * math.cos(ang)), h - 6 - int(ln * math.sin(ang)))
                mid = ((x0 + tip[0]) // 2, (h - 6 + tip[1]) // 2 - 7)
                pygame.draw.polygon(self.static, rng.choice([(14, 58, 34), (22, 80, 44), (10, 44, 28)]),
                                    [(x0, h), tip, mid])

        self.flies = [[rng.uniform(0, w), rng.uniform(70, 150), rng.uniform(0, 6.28)] for _ in range(22)]
        self.mist = [[rng.uniform(0, w), rng.randint(100, 140), rng.randint(40, 90)] for _ in range(6)]
        self.bird_t = 3.0

    @staticmethod
    def _fern(surf, x, y, rng):
        col = rng.choice([(40, 124, 62), (56, 150, 70), (28, 96, 50)])
        for ang in (-70, -40, -10, 20, 50, 80):
            a = math.radians(ang - 90)
            pygame.draw.line(surf, col, (x, y), (x + int(9 * math.cos(a)), y + int(9 * math.sin(a)) // 1))

    def draw(self, screen: pygame.Surface, t: float) -> None:
        s = self.work
        s.blit(self.static, (0, 0))
        for k in range(0, 60, 3):  # shimmering waterfall
            if (k // 3 + int(t * 8)) % 2 == 0:
                s.fill((226, 250, 244), (self.fall_x - 1, self.fall_top + k, 3, 2))
        self.beams.fill((0, 0, 0, 0))
        for i, bx in enumerate((40, 96, 150, 214)):  # light shafts slowly breathing
            alpha = 26 + int(14 * math.sin(t * 0.7 + i))
            pygame.draw.polygon(self.beams, (255, 240, 170, alpha),
                                [(bx, 0), (bx + 12, 0), (bx - 22, 150), (bx - 40, 150)])
        s.blit(self.beams, (0, 0))
        for m in self.mist:  # drifting mist
            x = (m[0] + t * 3) % (PIXEL_W + 100) - 50
            mist = pygame.Surface((m[2], 6), pygame.SRCALPHA)
            pygame.draw.ellipse(mist, (210, 235, 220, 40), mist.get_rect())
            s.blit(mist, (x, m[1]))
        for fly in self.flies:  # fireflies
            if math.sin(t * 2 + fly[2]) > -0.1:
                fx = fly[0] + 5 * math.sin(t * 0.8 + fly[2])
                fy = fly[1] + 4 * math.cos(t * 1.1 + fly[2])
                s.set_at((int(fx) % PIXEL_W, int(fy) % PIXEL_H), (230, 255, 120))
        phase = (t % 16) / 16  # a macaw crosses every 16 seconds
        if phase < 0.5:
            bx, by = phase * 2 * (PIXEL_W + 30) - 15, 28 + 6 * math.sin(phase * 40)
            flap = 2 if int(t * 8) % 2 else -2
            pygame.draw.line(s, (220, 40, 40), (bx - 3, by + flap), (bx, by), 1)
            pygame.draw.line(s, (40, 110, 220), (bx + 3, by + flap), (bx, by), 1)
            s.set_at((int(bx), int(by)), (250, 210, 60))
        pygame.transform.scale(s, (SCREEN_W, SCREEN_H), screen)


ForestBackground = JungleBackground  # backwards-compatible name used by older screens
