"""Tile-based world: layout, solidity queries and rendering."""
import pygame

from game.tiles import SOLID, TileSet
from settings import TILE


class World:
    def __init__(self, layout: list[str], spawn: tuple[int, int]):
        self.layout = layout
        self.h = len(layout)
        self.w = len(layout[0])
        self.spawn = spawn
        self.tileset = TileSet()
        self.pixel_size = (self.w * TILE, self.h * TILE)
        self.blockers: set[tuple[int, int]] = set()  # tiles blocked by solid objects

    def tile_at(self, tx: int, ty: int) -> str:
        if 0 <= tx < self.w and 0 <= ty < self.h:
            return self.layout[ty][tx]
        return "T"  # outside the map behaves like a wall of trees

    def is_solid(self, tx: int, ty: int) -> bool:
        return self.tile_at(tx, ty) in SOLID or (tx, ty) in self.blockers

    def draw(self, screen: pygame.Surface, cam_x: float, cam_y: float, t: float) -> None:
        sw, sh = screen.get_size()
        x0, y0 = max(0, int(cam_x // TILE)), max(0, int(cam_y // TILE))
        x1, y1 = min(self.w, int((cam_x + sw) // TILE) + 1), min(self.h, int((cam_y + sh) // TILE) + 1)
        for ty in range(y0, y1):
            row = self.layout[ty]
            for tx in range(x0, x1):
                ch = "." if row[tx] == "T" else row[tx]  # trees are drawn depth-sorted
                screen.blit(self.tileset.get(ch, t),
                            (tx * TILE - round(cam_x), ty * TILE - round(cam_y)))

    def visible_trees(self, cam_x: float, cam_y: float, sw: int, sh: int):
        """Yield (sort_y, sprite, world_pos) for trees in view."""
        x0, y0 = max(0, int(cam_x // TILE) - 1), max(0, int(cam_y // TILE))
        x1, y1 = min(self.w, int((cam_x + sw) // TILE) + 2), min(self.h, int((cam_y + sh) // TILE) + 2)
        for ty in range(y0, y1):
            row = self.layout[ty]
            for tx in range(x0, x1):
                if row[tx] == "T":
                    sprite = self.tileset.trees[(tx * 7 + ty * 13) % 3]
                    yield ((ty + 1) * TILE, sprite, (tx * TILE, ty * TILE - TILE // 2))
