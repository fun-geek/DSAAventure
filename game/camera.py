"""Smooth follow camera clamped to the world bounds."""
import pygame


class Camera:
    def __init__(self, view_size, world_size):
        self.view = pygame.Vector2(view_size)
        self.world = pygame.Vector2(world_size)
        self.pos = pygame.Vector2()

    def _target(self, center) -> pygame.Vector2:
        t = pygame.Vector2(center) - self.view / 2
        t.x = max(0, min(t.x, self.world.x - self.view.x))
        t.y = max(0, min(t.y, self.world.y - self.view.y))
        return t

    def snap(self, center) -> None:
        self.pos = self._target(center)

    def follow(self, center, dt: float) -> None:
        self.pos += (self._target(center) - self.pos) * min(1.0, dt * 8)
