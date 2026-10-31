"""Base class for all screens (menu, world select, gameplay, ...)."""
import pygame


class Scene:
    def __init__(self, game):
        self.game = game

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        pass

    def on_resume(self) -> None:
        """Called when a scene above this one is popped."""
