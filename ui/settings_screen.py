"""Settings: SFX volume and fullscreen, both persisted in SQLite."""
import pygame

from game.scene import Scene
from settings import COLORS, SCREEN_W
from ui.background import ForestBackground
from ui.widgets import Button, ButtonGroup, draw_panel, draw_text


class SettingsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.bg = ForestBackground()
        self.t = 0.0
        x = (SCREEN_W - 360) // 2
        self.vol_btn = Button("", (x, 250, 360, 50), self._cycle_volume)
        self.fs_btn = Button("", (x, 316, 360, 50), self._toggle_fullscreen)
        self.back_btn = Button("Back", (x, 400, 360, 50), self._back)
        self.group = ButtonGroup([self.vol_btn, self.fs_btn, self.back_btn], game.audio)
        self._relabel()

    def _relabel(self):
        self.vol_btn.label = f"SFX Volume: {round(self.game.audio.volume * 100)}%"
        self.fs_btn.label = f"Fullscreen: {'ON' if self.game.fullscreen else 'OFF'}"

    def _adjust_volume(self, delta: float):
        vol = round(min(1.0, max(0.0, self.game.audio.volume + delta)), 2)
        self.game.set_sfx_volume(vol)
        self.game.audio.play("select")
        self._relabel()

    def _cycle_volume(self):  # click: +10%, wrapping from 100% to 0%
        vol = self.game.audio.volume
        self._adjust_volume(-1.0 if vol >= 0.995 else 0.1)

    def _toggle_fullscreen(self):
        self.game.set_fullscreen(not self.game.fullscreen)
        self._relabel()

    def _back(self):
        self.game.pop()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.audio.play("back")
                self._back()
                return
            if self.group.index == 0 and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self._adjust_volume(0.1 if event.key == pygame.K_RIGHT else -0.1)
                return
        self.group.handle_event(event)

    def update(self, dt):
        self.t += dt

    def draw(self, screen):
        self.bg.draw(screen, self.t)
        panel = pygame.Rect(0, 0, 520, 380)
        panel.center = (SCREEN_W // 2, 320)
        draw_panel(screen, panel)
        draw_text(screen, "SETTINGS", 56, COLORS["title"], (panel.centerx, panel.y + 46),
                  "center")
        self.group.draw(screen)
        draw_text(screen, "Left/Right adjusts volume", 20, COLORS["text_dim"],
                  (panel.centerx, panel.bottom - 28), "center")
