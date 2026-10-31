"""Axis-separated AABB collision against solid tiles."""
import pygame

from settings import TILE


def _tiles_overlapping(world, left, top, right, bottom):
    for ty in range(int(top // TILE), int((bottom - 1e-6) // TILE) + 1):
        for tx in range(int(left // TILE), int((right - 1e-6) // TILE) + 1):
            if world.is_solid(tx, ty):
                yield tx, ty


def move_and_collide(pos: pygame.Vector2, size, delta: pygame.Vector2, world) -> pygame.Vector2:
    """Move a box (top-left `pos`, `size`) by `delta`, sliding along solid tiles."""
    w, h = size
    x, y = pos.x + delta.x, pos.y
    for tx, _ in _tiles_overlapping(world, x, y, x + w, y + h):
        x = tx * TILE - w if delta.x > 0 else (tx + 1) * TILE
    y += delta.y
    for _, ty in _tiles_overlapping(world, x, y, x + w, y + h):
        y = ty * TILE - h if delta.y > 0 else (ty + 1) * TILE
    return pygame.Vector2(x, y)
