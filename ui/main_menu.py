"""Main menu and the name-entry screen used by New Game."""
import math

import pygame

from game.scene import Scene
from settings import COLORS, SCREEN_H, SCREEN_W, VERSION
from ui.background import ForestBackground
from ui.profile import ProfileScene
from ui.settings_screen import SettingsScene
from ui.widgets import Button, ButtonGroup, draw_panel, draw_text
from ui.world_select import WorldSelectScene

BTN_W, BTN_H, BTN_GAP, BTN_TOP = 320, 46, 10, 250


class MainMenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.bg = ForestBackground()
        self.t = 0.0
        self.dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.dim.fill((4, 18, 10, 80))
        entries = [("New Game", self._new_game), ("Continue", self._continue),
                   ("Select World", self._select_world), ("Player Profile", self._profile),
                   ("Settings", self._settings), ("Exit", self._exit)]
        x = (SCREEN_W - BTN_W) // 2
        self.buttons = [Button(label, (x, BTN_TOP + i * (BTN_H + BTN_GAP), BTN_W, BTN_H), cb)
                        for i, (label, cb) in enumerate(entries)]
        self.group = ButtonGroup(self.buttons, game.audio)
        self.on_resume()

    def on_resume(self) -> None:
        """Enable save-dependent buttons only when a save exists."""
        has_save = self.game.db.has_save()
        for b in self.buttons[1:4]:
            b.enabled = has_save
        self.group.ensure_valid()

    # ---- actions ---------------------------------------------------------
    def _new_game(self):
        self.game.push(NameInputScene(self.game))

    def _continue(self):
        self.game.db.touch_login()
        self.game.push(WorldSelectScene(self.game))

    def _select_world(self):
        self.game.push(WorldSelectScene(self.game))

    def _profile(self):
        self.game.push(ProfileScene(self.game))

    def _settings(self):
        self.game.push(SettingsScene(self.game))

    def _exit(self):
        self.game.running = False

    # ---- loop ------------------------------------------------------------
    def handle_event(self, event):
        self.group.handle_event(event)

    def update(self, dt):
        self.t += dt

    def draw(self, screen):
        self.bg.draw(screen, self.t)
        screen.blit(self.dim, (0, 0))
        bob = int(4 * math.sin(self.t * 2))
        draw_text(screen, "DSA JUNGLE", 104, COLORS["title"], (SCREEN_W // 2, 78 + bob),
                  "center", shadow=True)
        draw_text(screen, "SOLVER", 104, COLORS["text"], (SCREEN_W // 2, 148 + bob),
                  "center", shadow=True)
        draw_text(screen, "Explore the wild. Crack the code. Conquer algorithms.", 26, COLORS["text"],
                  (SCREEN_W // 2, 208), "center", shadow=True)
        self.group.draw(screen)
        player = self.game.db.get_player()
        if player:
            draw_text(screen, f"Welcome back, {player['name']}!", 24, COLORS["title"],
                      (SCREEN_W // 2, SCREEN_H - 48), "center", shadow=True)
        draw_text(screen, f"v{VERSION}", 20, COLORS["text_dim"], (10, SCREEN_H - 24))


class NameInputScene(Scene):
    MAX_LEN = 16

    def __init__(self, game):
        super().__init__(game)
        self.bg = ForestBackground()
        self.t = 0.0
        self.name = ""
        self.overwrite = game.db.has_save()
        pygame.key.start_text_input()

    def _close(self):
        pygame.key.stop_text_input()
        self.game.pop()

    def handle_event(self, event):
        if event.type == pygame.TEXTINPUT:
            if len(self.name) < self.MAX_LEN and event.text.isprintable():
                self.name += event.text
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.audio.play("back")
                self._close()
            elif event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.name.strip():
                self.game.audio.play("select")
                self.game.db.create_player(self.name)
                pygame.key.stop_text_input()
                self.game.pop()  # back to menu (refreshes buttons)
                self.game.push(WorldSelectScene(self.game))

    def update(self, dt):
        self.t += dt

    def draw(self, screen):
        self.bg.draw(screen, self.t)
        panel = pygame.Rect(0, 0, 560, 260)
        panel.center = (SCREEN_W // 2, SCREEN_H // 2)
        draw_panel(screen, panel)
        draw_text(screen, "NEW ADVENTURE", 48, COLORS["title"], (panel.centerx, panel.y + 44),
                  "center")
        draw_text(screen, "Enter your hero's name:", 28, COLORS["text"],
                  (panel.centerx, panel.y + 94), "center")
        box = pygame.Rect(0, 0, 360, 48)
        box.center = (panel.centerx, panel.y + 140)
        pygame.draw.rect(screen, COLORS["border"], box)
        pygame.draw.rect(screen, (14, 10, 24), box.inflate(-6, -6))
        cursor = "_" if int(self.t * 2) % 2 == 0 else " "
        draw_text(screen, self.name + cursor, 34, COLORS["text"], box.center, "center")
        hint = "Enter: start   Esc: cancel"
        draw_text(screen, hint, 22, COLORS["text_dim"], (panel.centerx, panel.bottom - 56),
                  "center")
        if self.overwrite:
            draw_text(screen, "Warning: this replaces your existing save!", 22,
                      COLORS["warn"], (panel.centerx, panel.bottom - 30), "center")
