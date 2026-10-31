"""Player: procedural 4-direction walk-cycle sprite, movement and collision."""
import pygame

from game.animation import Animator
from game.collision import move_and_collide
from settings import PLAYER_RUN_MULT, PLAYER_SPEED, TILE

HIT_W, HIT_H = 20, 14
DIRS = ("down", "up", "left", "right")


def _frame(direction: str, step: int, pal: dict | None = None) -> pygame.Surface:
    """Draw one 16x16 frame, then scale 2x. step: 0 idle, 1/2 alternating legs."""
    s = pygame.Surface((16, 16), pygame.SRCALPHA)
    pal = pal or {}
    skin, hair = pal.get("skin", (240, 200, 160)), pal.get("hair", (96, 60, 36))
    tunic, dark = pal.get("tunic", (196, 140, 64)), pal.get("dark", (140, 96, 40))
    hat, hat_d = pal.get("hat", (222, 192, 120)), pal.get("hat_dark", (150, 118, 64))
    boots, trousers = (70, 48, 36), pal.get("trousers", (74, 96, 62))
    # legs (the stepping leg lifts one pixel)
    lift_l, lift_r = (1 if step == 1 else 0), (1 if step == 2 else 0)
    pygame.draw.rect(s, boots, (5, 13, 3, 3 - lift_l))
    pygame.draw.rect(s, boots, (8, 13, 3, 3 - lift_r))
    pygame.draw.rect(s, trousers, (5, 11, 6, 2))  # trousers
    # tunic + arms
    pygame.draw.rect(s, tunic, (4, 7, 8, 5))
    pygame.draw.rect(s, dark, (4, 11, 8, 1))
    arm_y = 8 + (1 if step else 0)
    if direction in ("down", "up"):
        pygame.draw.rect(s, skin, (3, arm_y, 1, 3))
        pygame.draw.rect(s, skin, (12, arm_y, 1, 3))
    else:
        pygame.draw.rect(s, skin, (7, arm_y, 2, 3))
    # head
    pygame.draw.rect(s, skin, (4, 2, 8, 6))
    if direction == "up":
        pygame.draw.rect(s, hair, (4, 2, 8, 6))
    else:
        pygame.draw.rect(s, hair, (4, 2, 8, 2))
        if direction == "down":
            s.set_at((6, 5), (30, 30, 40)); s.set_at((9, 5), (30, 30, 40))
        elif direction == "left":
            pygame.draw.rect(s, hair, (9, 2, 3, 5)); s.set_at((5, 5), (30, 30, 40))
        else:
            pygame.draw.rect(s, hair, (4, 2, 3, 5)); s.set_at((10, 5), (30, 30, 40))
    # explorer's pith helmet: crown, brim and a band
    pygame.draw.rect(s, hat, (4, 0, 8, 3))
    pygame.draw.rect(s, hat, (2, 2, 12, 1))
    pygame.draw.rect(s, hat_d, (4, 2, 8, 1))
    if direction == "down":
        pygame.draw.rect(s, hat_d, (2, 3, 12, 1))
    return pygame.transform.scale(s, (TILE, TILE))


class Player:
    def __init__(self, spawn_tile: tuple[int, int]):
        self.frames = {d: [_frame(d, i) for i in range(3)] for d in DIRS}
        self.facing = "down"
        self.anim = Animator()
        self.moving = False
        tx, ty = spawn_tile
        self.pos = pygame.Vector2(tx * TILE + (TILE - HIT_W) / 2, ty * TILE + TILE - HIT_H)

    @property
    def hitbox(self) -> pygame.Rect:
        return pygame.Rect(round(self.pos.x), round(self.pos.y), HIT_W, HIT_H)

    @property
    def center(self) -> pygame.Vector2:
        return pygame.Vector2(self.pos.x + HIT_W / 2, self.pos.y + HIT_H / 2)

    def update(self, dt: float, direction: pygame.Vector2, running: bool, world) -> None:
        self.moving = direction.length_squared() > 0
        mult = PLAYER_RUN_MULT if running else 1.0
        if self.moving:
            direction = direction.normalize()
            if abs(direction.x) > abs(direction.y):
                self.facing = "right" if direction.x > 0 else "left"
            else:
                self.facing = "down" if direction.y > 0 else "up"
            self.pos = move_and_collide(self.pos, (HIT_W, HIT_H),
                                        direction * PLAYER_SPEED * mult * dt, world)
        self.anim.update(dt, self.moving, mult)

    def draw(self, screen, cam) -> None:
        hb = self.hitbox
        sx, sy = hb.centerx - round(cam.pos.x), hb.bottom - round(cam.pos.y)
        shadow = pygame.Surface((22, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), shadow.get_rect())
        screen.blit(shadow, (sx - 11, sy - 6))
        screen.blit(self.frames[self.facing][self.anim.frame], (sx - TILE // 2, sy - TILE + 4))
