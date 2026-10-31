"""Problem list for one world: shows difficulty, solved modes, and opens a challenge."""
import pygame

from game.scene import Scene
from settings import COLORS, SCREEN_H, SCREEN_W, WORLDS
from ui.background import JungleBackground
from ui.challenge_screen import DIFF_COLOR, ChallengeScene
from ui.widgets import Button, draw_panel, draw_text

ROW_H = 56


class ProblemListScene(Scene):
    def __init__(self, game, world_id: int):
        super().__init__(game)
        self.bg = JungleBackground()
        self.t = 0.0
        self.world = next(w for w in WORLDS if w["id"] == world_id)
        self.questions = game.challenges.bank.for_world(world_id)
        self.sel = 0
        self.progress = {}
        self.back = Button("Back", ((SCREEN_W - 200) // 2, 560, 200, 46), game.pop)
        self.on_resume()

    def on_resume(self):
        self.progress = self.game.db.get_challenge_progress()

    def _open(self):
        self.game.audio.play("select")
        self.game.push(ChallengeScene(self.game, self.questions[self.sel]))

    def _rects(self):
        return [pygame.Rect(120, 120 + i * (ROW_H + 8), SCREEN_W - 240, ROW_H) for i in range(len(self.questions))]

    def handle_event(self, event):
        n = len(self.questions)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.audio.play("back")
                self.game.pop()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % n
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % n
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._open()
        elif event.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self._rects()):
                if r.collidepoint(event.pos):
                    self.sel = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back.rect.collidepoint(event.pos):
                self.game.audio.play("back")
                self.game.pop()
            for i, r in enumerate(self._rects()):
                if r.collidepoint(event.pos):
                    self.sel = i
                    self._open()

    def update(self, dt):
        self.t += dt

    def draw(self, screen):
        self.bg.draw(screen, self.t)
        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((4, 16, 10, 150))
        screen.blit(dim, (0, 0))
        draw_text(screen, self.world["name"].upper(), 52, COLORS["title"], (SCREEN_W // 2, 52), "center", shadow=True)
        draw_text(screen, "Pick a puzzle. Beginner, Intermediate and Advanced modes each pay out once.", 22,
                  COLORS["text"], (SCREEN_W // 2, 92), "center", shadow=True)
        for i, (q, r) in enumerate(zip(self.questions, self._rects())):
            draw_panel(screen, r, edge=COLORS["btn_focus"] if i == self.sel else None, vines=False)
            draw_text(screen, f"{i + 1}.", 28, COLORS["text_dim"], (r.x + 24, r.centery), "midleft")
            draw_text(screen, q["title"], 28, COLORS["text"], (r.x + 64, r.centery), "midleft")
            draw_text(screen, q["difficulty"].upper(), 20, DIFF_COLOR[q["difficulty"]], (r.right - 250, r.centery), "midleft")
            solved = self.progress.get(q["id"], {})
            for k, (letter, mode) in enumerate((("B", "beginner"), ("I", "intermediate"), ("A", "advanced"))):
                cx = r.right - 120 + k * 34
                ok = solved.get(mode, False)
                pygame.draw.circle(screen, (120, 230, 120) if ok else (60, 66, 56), (cx, r.centery), 13)
                draw_text(screen, letter, 20, (20, 40, 20) if ok else COLORS["text_dim"], (cx, r.centery), "center")
        self.back.draw(screen, False)
