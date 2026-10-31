"""Reusable UI helpers: text drawing, buttons, keyboard/mouse button groups."""
import pygame

from settings import COLORS


class Fonts:
    _cache: dict[int, pygame.font.Font] = {}

    @classmethod
    def get(cls, size: int) -> pygame.font.Font:
        if size not in cls._cache:
            cls._cache[size] = pygame.font.Font(None, size)
        return cls._cache[size]


    _mono: dict[int, pygame.font.Font] = {}

    @classmethod
    def mono(cls, size: int) -> pygame.font.Font:
        if size not in cls._mono:
            cls._mono[size] = pygame.font.SysFont(
                "dejavusansmono,consolas,menlo,couriernew,monospace", size)
        return cls._mono[size]

    @classmethod
    def reset(cls) -> None:
        """Drop cached fonts (they become invalid after pygame.quit())."""
        cls._cache.clear()
        cls._mono.clear()


def draw_text(surface, text, size, color, pos, anchor="topleft", shadow=False):
    font = Fonts.get(size)
    if shadow:
        sh = font.render(text, False, COLORS["shadow"])
        surface.blit(sh, sh.get_rect(**{anchor: (pos[0] + 3, pos[1] + 3)}))
    img = font.render(text, False, color)
    rect = img.get_rect(**{anchor: pos})
    surface.blit(img, rect)
    return rect


def _leaf(surface, x, y, dx, dy, size=9):
    """A tiny pixel leaf pointing in direction (dx, dy)."""
    pts = [(x, y), (x + dx * size, y + dy * size // 3), (x + dx * size // 2, y + dy * size)]
    pygame.draw.polygon(surface, (34, 110, 52), pts)
    pygame.draw.line(surface, (110, 190, 80), (x, y), (x + dx * size // 2, y + dy * size // 3))


def draw_vines(surface, rect, seed=0):
    """Hanging vines and leaves that frame a panel's corners."""
    for i, (cx, cy, dx, dy) in enumerate(((rect.left, rect.top, 1, 1), (rect.right, rect.top, -1, 1),
                                          (rect.left, rect.bottom, 1, -1), (rect.right, rect.bottom, -1, -1))):
        length = 22 + (seed + i * 7) % 14
        pygame.draw.line(surface, (30, 96, 46), (cx, cy), (cx + dx * 2, cy + dy * length), 3)
        pygame.draw.line(surface, (30, 96, 46), (cx, cy), (cx + dx * length, cy + dy * 2), 3)
        for k in range(1, 4):
            _leaf(surface, cx + dx * 2, cy + dy * k * length // 4, dx, 1 if k % 2 else -1, 8)
            _leaf(surface, cx + dx * k * length // 4, cy + dy * 2, 1 if k % 2 else -1, dy, 8)


def draw_panel(surface, rect, fill=None, edge=None, vines=True):
    """Wooden frame with a mossy interior and vine corners."""
    pygame.draw.rect(surface, COLORS["border"], rect)
    frame = rect.inflate(-4, -4)
    pygame.draw.rect(surface, edge or COLORS["panel_edge"], frame)
    for y in range(frame.top + 3, frame.bottom - 2, 6):  # wood grain
        pygame.draw.line(surface, (104, 70, 38), (frame.left + 2, y), (frame.right - 3, y))
    inner = rect.inflate(-12, -12)
    pygame.draw.rect(surface, COLORS["border"], inner.inflate(2, 2))
    pygame.draw.rect(surface, fill or COLORS["panel"], inner)
    if vines and rect.w >= 120 and rect.h >= 60:
        draw_vines(surface, rect, rect.x + rect.y)


class Button:
    def __init__(self, label, rect, on_click, enabled=True):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.on_click = on_click
        self.enabled = enabled

    def draw(self, surface, focused: bool) -> None:
        if not self.enabled:
            fill, text, light = COLORS["btn_disabled"], COLORS["text_disabled"], (84, 76, 64)
        elif focused:
            fill, text, light = COLORS["btn_focus"], COLORS["btn_text_focus"], (255, 236, 150)
        else:
            fill, text, light = COLORS["btn"], COLORS["text"], (150, 108, 62)
        pygame.draw.rect(surface, COLORS["border"], self.rect)
        inner = self.rect.inflate(-8, -8)
        pygame.draw.rect(surface, fill, inner)
        pygame.draw.line(surface, light, inner.topleft, inner.topright, 3)            # lit top edge
        pygame.draw.line(surface, tuple(c * 2 // 3 for c in fill), inner.bottomleft,  # shaded bottom
                         inner.bottomright, 3)
        for x in (inner.left + 8, inner.right - 8):                                    # rope studs
            pygame.draw.circle(surface, COLORS["border"], (x, inner.centery), 3)
        draw_text(surface, self.label, 30, text, self.rect.center, "center")
        if focused and self.enabled:  # glowing jungle leaves flank the focused plank
            for sign, x in ((-1, self.rect.left - 6), (1, self.rect.right + 6)):
                _leaf(surface, x, self.rect.centery - 8, sign, 1, 14)
                _leaf(surface, x, self.rect.centery + 8, sign, -1, 14)


class ButtonGroup:
    """Keyboard (up/down/enter) and mouse navigation over a list of buttons."""

    def __init__(self, buttons, audio=None):
        self.buttons = buttons
        self.audio = audio
        self.index = 0
        self.ensure_valid()

    def ensure_valid(self) -> None:
        if not self.buttons[self.index].enabled:
            self._move(1)

    def _move(self, step: int) -> None:
        n = len(self.buttons)
        for i in range(1, n + 1):
            j = (self.index + step * i) % n
            if self.buttons[j].enabled:
                self.index = j
                return

    def _activate(self, button: Button) -> None:
        if self.audio:
            self.audio.play("select")
        button.on_click()

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            for i, b in enumerate(self.buttons):
                if b.enabled and b.rect.collidepoint(event.pos) and i != self.index:
                    self.index = i
                    if self.audio:
                        self.audio.play("move")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, b in enumerate(self.buttons):
                if b.enabled and b.rect.collidepoint(event.pos):
                    self.index = i
                    self._activate(b)
                    return True
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._move(-1)
                if self.audio:
                    self.audio.play("move")
                return True
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self._move(1)
                if self.audio:
                    self.audio.play("move")
                return True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._activate(self.buttons[self.index])
                return True
        return False

    def draw(self, surface) -> None:
        for i, b in enumerate(self.buttons):
            b.draw(surface, i == self.index)
