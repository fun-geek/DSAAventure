"""World selection grid. Locked/unlocked state comes from the SQLite save."""
import pygame

from game.scene import Scene
from settings import COLORS, PRACTICE_ALL_WORLDS, SCREEN_H, SCREEN_W, WORLDS
from ui.background import ForestBackground
from ui.game_scene import GameScene
from ui.problem_list import ProblemListScene
from ui.widgets import Button, draw_panel, draw_text
from worlds import WORLD_MAPS

COLS, CARD_W, CARD_H, GAP = 3, 280, 150, 20


class WorldSelectScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.bg = ForestBackground()
        self.t = 0.0
        self.sel = 0
        self.toast, self.toast_t = "", 0.0
        self.progress = game.db.get_world_progress()
        left = (SCREEN_W - (COLS * CARD_W + (COLS - 1) * GAP)) // 2
        self.cards = [pygame.Rect(left + (i % COLS) * (CARD_W + GAP),
                                  130 + (i // COLS) * (CARD_H + GAP), CARD_W, CARD_H)
                      for i in range(len(WORLDS))]
        self.back = Button("Back", (240, 520, 190, 46), self._back)
        self.practice = Button("Practice Puzzles (P)", (460, 520, 260, 46), self._practice)

    def _back(self):
        self.game.pop()

    def _practice(self):
        i = self.sel
        if self._unlocked(i) or PRACTICE_ALL_WORLDS:
            self.game.audio.play("select")
            self.game.push(ProblemListScene(self.game, WORLDS[i]["id"]))
        else:
            self.game.audio.play("back")
            self.toast, self.toast_t = f"{WORLDS[i]['name']} is locked.", 3.0

    def _unlocked(self, i) -> bool:
        return self.progress.get(WORLDS[i]["id"], {}).get("unlocked", False)

    def _enter(self, i):
        world = WORLDS[i]
        if self._unlocked(i):
            self.game.audio.play("select")
            if world["id"] in WORLD_MAPS:
                self.game.push(GameScene(self.game, world["id"]))
                return
            self.toast = f"{world['name']}: map arrives in a later phase - press P to practise its puzzles!"
        else:
            self.game.audio.play("back")
            self.toast = f"{world['name']} is locked. Defeat the previous boss first."
        self.toast_t = 3.0

    def handle_event(self, event):
        n = len(WORLDS)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.audio.play("back")
                self._back()
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.sel = (self.sel + 1) % n
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.sel = (self.sel - 1) % n
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + COLS) % n
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - COLS) % n
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._enter(self.sel)
            elif event.key == pygame.K_p:
                self._practice()
        elif event.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.cards):
                if r.collidepoint(event.pos):
                    self.sel = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back.rect.collidepoint(event.pos):
                self.game.audio.play("back")
                self._back()
                return
            if self.practice.rect.collidepoint(event.pos):
                return self._practice()
            for i, r in enumerate(self.cards):
                if r.collidepoint(event.pos):
                    self.sel = i
                    self._enter(i)

    def update(self, dt):
        self.t += dt
        self.toast_t = max(0.0, self.toast_t - dt)

    def draw(self, screen):
        self.bg.draw(screen, self.t)
        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((4, 16, 10, 150))
        screen.blit(dim, (0, 0))
        draw_text(screen, "SELECT WORLD", 60, COLORS["title"], (SCREEN_W // 2, 64),
                  "center", shadow=True)
        for i, (world, rect) in enumerate(zip(WORLDS, self.cards)):
            unlocked = self._unlocked(i)
            done = self.progress.get(world["id"], {}).get("completed", False)
            edge = COLORS["btn_focus"] if i == self.sel else (
                world["color"] if unlocked else COLORS["locked"])
            draw_panel(screen, rect, edge=edge)
            fg = COLORS["text"] if unlocked else COLORS["text_disabled"]
            draw_text(screen, f"World {world['id']}", 22, world["color"] if unlocked
                      else COLORS["text_disabled"], (rect.x + 18, rect.y + 18))
            draw_text(screen, world["name"], 27, fg, (rect.x + 18, rect.y + 44))
            draw_text(screen, f"Boss: {world['boss']}", 22, fg, (rect.x + 18, rect.y + 80))
            draw_text(screen, f"{world['problems']} problems", 22, COLORS["text_dim"],
                      (rect.x + 18, rect.y + 104))
            status = "COMPLETED" if done else ("UNLOCKED" if unlocked else "LOCKED")
            draw_text(screen, status, 20, COLORS["xp_bar"] if unlocked else COLORS["warn"],
                      (rect.right - 16, rect.bottom - 24), "midright")
        self.back.draw(screen, False)
        self.practice.draw(screen, False)
        if self.toast_t > 0:
            draw_text(screen, self.toast, 26, COLORS["title"], (SCREEN_W // 2, 600),
                      "center", shadow=True)
        else:
            draw_text(screen, "Arrows/mouse: choose   Enter: explore   P: puzzles   Esc: back", 22,
                      COLORS["text_dim"], (SCREEN_W // 2, 600), "center")
