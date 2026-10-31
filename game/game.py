"""Game core: window, scene stack, main loop."""
import pygame

from challenges.challenge_engine import ChallengeEngine, QuestionBank
from game.scene import Scene
from settings import DB_PATH, FPS, SCREEN_H, SCREEN_W, TITLE
from systems.audio import Audio
from systems.database import Database
from ui.main_menu import MainMenuScene
from ui.widgets import Fonts


class Game:
    def __init__(self, db_path=None):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.db = Database(db_path or DB_PATH)
        self.fullscreen = self.db.get_setting("fullscreen", "0") == "1"
        self.screen = self._make_display()
        self.clock = pygame.time.Clock()
        self.audio = Audio(float(self.db.get_setting("sfx_volume", "0.7")))
        self.challenges = ChallengeEngine(QuestionBank.load())
        self.drafts: dict = {}  # unsaved code per (question, mode), kept while the game runs
        self.running = True
        self.scenes: list[Scene] = []
        self._fade = 0.0
        self._fade_surface = pygame.Surface((SCREEN_W, SCREEN_H))
        self.push(MainMenuScene(self))

    # ---- display / settings ---------------------------------------------
    def _make_display(self) -> pygame.Surface:
        extra = pygame.FULLSCREEN if self.fullscreen else 0
        try:  # SCALED keeps the 960x640 logical size in any window/fullscreen
            return pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED | extra)
        except pygame.error:  # e.g. no GPU renderer: fall back to plain mode
            return pygame.display.set_mode((SCREEN_W, SCREEN_H), extra)

    def set_fullscreen(self, value: bool) -> None:
        self.fullscreen = value
        self.screen = self._make_display()
        self.db.set_setting("fullscreen", "1" if value else "0")

    def set_sfx_volume(self, volume: float) -> None:
        self.audio.set_volume(volume)
        self.db.set_setting("sfx_volume", f"{self.audio.volume:.2f}")

    # ---- scene stack -----------------------------------------------------
    @property
    def scene(self) -> Scene:
        return self.scenes[-1]

    def push(self, scene: Scene) -> None:
        self.scenes.append(scene)
        self._fade = 1.0

    def pop(self) -> None:
        self.scenes.pop()
        self._fade = 1.0
        if self.scenes:
            self.scene.on_resume()

    # ---- loop ------------------------------------------------------------
    def tick(self, dt: float) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.scenes:
                self.scene.handle_event(event)
        if not self.scenes:
            self.running = False
            return
        self.scene.update(dt)
        self.scene.draw(self.screen)
        if self._fade > 0:  # smooth fade-in after scene changes
            self._fade = max(0.0, self._fade - dt * 4)
            self._fade_surface.set_alpha(int(255 * self._fade))
            self.screen.blit(self._fade_surface, (0, 0))
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.tick(self.clock.tick(FPS) / 1000)

    def shutdown(self) -> None:
        self.db.close()
        Fonts.reset()
        pygame.quit()
