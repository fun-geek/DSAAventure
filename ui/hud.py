"""In-game HUD: name/level, XP bar, coins, location."""
import pygame

from settings import COLORS, SCREEN_W
from systems.progression import level_from_xp, xp_into_level
from ui.widgets import draw_panel, draw_text


def draw_hud(screen: pygame.Surface, player: dict, location: str) -> None:
    panel = pygame.Rect(10, 10, 270, 84)
    draw_panel(screen, panel)
    xp = player["xp"]
    cur, need = xp_into_level(xp)
    draw_text(screen, player["name"], 26, COLORS["title"], (panel.x + 16, panel.y + 14))
    draw_text(screen, f"Lv {level_from_xp(xp)}", 24, COLORS["text"], (panel.right - 16, panel.y + 14), "topright")
    bar = pygame.Rect(panel.x + 16, panel.y + 40, panel.w - 32, 14)
    pygame.draw.rect(screen, COLORS["border"], bar.inflate(4, 4))
    pygame.draw.rect(screen, COLORS["xp_back"], bar)
    pygame.draw.rect(screen, COLORS["xp_bar"], (bar.x, bar.y, int(bar.w * cur / need), bar.h))
    draw_text(screen, f"XP {cur}/{need}", 18, COLORS["text"], bar.center, "center")
    pygame.draw.rect(screen, (255, 214, 102), (panel.x + 16, panel.y + 62, 10, 10))
    draw_text(screen, f"{player['coins']} coins", 22, COLORS["text"], (panel.x + 34, panel.y + 60))
    loc = pygame.Rect(0, 10, 300, 40)
    loc.right = SCREEN_W - 10
    draw_panel(screen, loc)
    draw_text(screen, location, 26, COLORS["text"], loc.center, "center")
