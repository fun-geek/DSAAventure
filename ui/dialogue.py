"""Typewriter dialogue box (reused by NPCs in Phase 4)."""
import pygame

from settings import COLORS, SCREEN_H, SCREEN_W
from ui.widgets import Fonts, draw_panel, draw_text


def wrap_text(text: str, size: int, max_width: int) -> list[str]:
    font, lines, line = Fonts.get(size), [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if font.size(trial)[0] <= max_width:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line] if line else lines


class DialogueBox:
    CHARS_PER_SEC = 55

    def __init__(self):
        self.active = False
        self.speaker, self.text, self.shown, self.t = "", "", 0.0, 0.0
        self.pages: list[str] = []
        self.page = 0
        self.on_close = None

    def show(self, speaker: str, text: str) -> None:
        self.show_lines(speaker, [text])

    def show_lines(self, speaker: str, lines: list[str], on_close=None) -> None:
        """Show several pages in a row; `on_close` runs after the last one."""
        self.speaker, self.pages, self.page, self.on_close = speaker, list(lines), 0, on_close
        self.text, self.shown, self.active = self.pages[0], 0.0, True

    def update(self, dt: float) -> bool:
        """Advance the typewriter; returns True while a new character appeared."""
        self.t += dt
        if self.active and self.shown < len(self.text):
            before = int(self.shown)
            self.shown = min(len(self.text), self.shown + dt * self.CHARS_PER_SEC)
            return int(self.shown) != before and self.text[int(self.shown) - 1:int(self.shown)] != " "
        return False

    def advance(self) -> None:
        """First press completes the line, second press closes the box."""
        if self.shown < len(self.text):
            self.shown = len(self.text)
        elif self.page + 1 < len(self.pages):
            self.page += 1
            self.text, self.shown = self.pages[self.page], 0.0
        else:
            self.active = False
            callback, self.on_close = self.on_close, None
            if callback:
                callback()

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
        panel = pygame.Rect(40, SCREEN_H - 170, SCREEN_W - 80, 150)
        draw_panel(screen, panel)
        draw_text(screen, self.speaker, 30, COLORS["title"], (panel.x + 26, panel.y + 20))
        visible = self.text[:int(self.shown)]
        # wrap the full text so words do not jump lines while typing
        y, used = panel.y + 56, 0
        for line in wrap_text(self.text, 28, panel.w - 56):
            part = visible[used:used + len(line) + 1].strip()
            draw_text(screen, part, 28, COLORS["text"], (panel.x + 26, y))
            used += len(line) + 1
            y += 30
        if self.shown >= len(self.text) and int(self.t * 2) % 2 == 0:
            draw_text(screen, "E / Space  >", 20, COLORS["text_dim"],
                      (panel.right - 22, panel.bottom - 22), "bottomright")
