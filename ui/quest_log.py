"""Quest tracker (HUD) and full quest log overlay."""
import pygame

from settings import COLORS, SCREEN_H, SCREEN_W
from ui.widgets import draw_panel, draw_text


def draw_quest_tracker(screen, qm, collected) -> None:
    panel = pygame.Rect(10, 104, 270, 74)
    draw_panel(screen, panel)
    q = qm.tracked(collected)
    draw_text(screen, "QUEST", 18, COLORS["text_dim"], (panel.x + 16, panel.y + 12))
    if q is None:
        done = all(qm.status(d["id"], collected) == "completed" for d in qm.defs)
        msg = "All quests complete!" if done else "Talk to villagers"
        draw_text(screen, msg, 24, COLORS["text"], (panel.x + 16, panel.y + 36))
        return
    cur, target = qm.progress(q, collected)
    ready = qm.status(q["id"], collected) == "ready"
    draw_text(screen, q["title"], 24, COLORS["title"], (panel.x + 16, panel.y + 30))
    text = "Return to the quest giver!" if ready else f"{q['objective']}  {cur}/{target}"
    draw_text(screen, text, 19, COLORS["xp_bar"] if ready else COLORS["text"],
              (panel.x + 16, panel.y + 52))


def draw_quest_log(screen, qm, collected) -> None:
    dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    dim.fill((10, 6, 24, 170))
    screen.blit(dim, (0, 0))
    panel = pygame.Rect(0, 0, 720, 470)
    panel.center = (SCREEN_W // 2, SCREEN_H // 2)
    draw_panel(screen, panel)
    draw_text(screen, "QUEST LOG", 48, COLORS["title"], (panel.centerx, panel.y + 40), "center")
    y = panel.y + 84
    shown = 0
    for q in qm.defs:
        status = qm.status(q["id"], collected)
        if status in ("locked", "available"):
            continue
        shown += 1
        cur, target = qm.progress(q, collected)
        label, color = {"active": (f"{cur}/{target}", COLORS["text"]),
                        "ready": ("Ready to turn in!", COLORS["xp_bar"]),
                        "completed": ("Completed", COLORS["text_dim"])}[status]
        draw_text(screen, q["title"], 28, COLORS["title"] if status != "completed"
                  else COLORS["text_dim"], (panel.x + 30, y))
        draw_text(screen, label, 24, color, (panel.right - 30, y + 2), "topright")
        draw_text(screen, f"{q['objective']}  -  reward: {q['xp']} XP, {q['coins']} coins", 20,
                  COLORS["text_dim"], (panel.x + 30, y + 30))
        y += 70
    if not shown:
        draw_text(screen, "No quests yet. Talk to the villagers!", 26, COLORS["text"],
                  panel.center, "center")
    draw_text(screen, "Q / Esc: close", 20, COLORS["text_dim"],
              (panel.centerx, panel.bottom - 24), "center")
