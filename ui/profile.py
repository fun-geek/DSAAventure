"""Player profile screen backed by the SQLite save."""
import pygame

from game.scene import Scene
from settings import COLORS, SCREEN_W, WORLDS
from systems.progression import level_from_xp, xp_into_level
from ui.background import ForestBackground
from ui.widgets import Button, draw_panel, draw_text


class ProfileScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.bg = ForestBackground()
        self.t = 0.0
        self.player = game.db.get_player()
        self.progress = game.db.get_world_progress()
        self.back = Button("Back", ((SCREEN_W - 200) // 2, 572, 200, 46), self._back)

    def _back(self):
        self.game.pop()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.game.audio.play("back")
            self._back()
        elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
              and self.back.rect.collidepoint(event.pos)):
            self.game.audio.play("back")
            self._back()

    def update(self, dt):
        self.t += dt

    def draw(self, screen):
        self.bg.draw(screen, self.t)
        panel = pygame.Rect(0, 0, 620, 480)
        panel.center = (SCREEN_W // 2, 300)
        draw_panel(screen, panel)
        draw_text(screen, "PLAYER PROFILE", 52, COLORS["title"], (panel.centerx, panel.y + 44),
                  "center")
        p = self.player
        if not p:
            draw_text(screen, "No save found.", 30, COLORS["text"], panel.center, "center")
        else:
            xp = p["xp"]
            cur, need = xp_into_level(xp)
            x, y = panel.x + 50, panel.y + 100
            rows = [("Name", p["name"]), ("Level", str(level_from_xp(xp))),
                    ("Coins", str(p["coins"])), ("Daily streak", f"{p['streak']} day(s)"),
                    ("Worlds unlocked",
                     f"{sum(v['unlocked'] for v in self.progress.values())} / {len(WORLDS)}"),
                    ("Quests completed", str(self.game.db.count_completed_quests())),
                    ("Puzzles solved", f"{len(self.game.db.solved_questions())} / {len(self.game.challenges.bank.questions)}"),
                    ("Started", p["created_at"])]
            for i, (k, v) in enumerate(rows):
                draw_text(screen, k, 28, COLORS["text_dim"], (x, y + i * 38))
                draw_text(screen, v, 28, COLORS["text"], (panel.right - 50, y + i * 38),
                          "topright")
            bar = pygame.Rect(x, panel.bottom - 70, panel.w - 100, 22)
            pygame.draw.rect(screen, COLORS["border"], bar.inflate(6, 6))
            pygame.draw.rect(screen, COLORS["xp_back"], bar)
            pygame.draw.rect(screen, COLORS["xp_bar"], (bar.x, bar.y, int(bar.w * cur / need),
                                                        bar.h))
            draw_text(screen, f"XP {cur} / {need}", 20, COLORS["text"], bar.center, "center")
        self.back.draw(screen, True)
