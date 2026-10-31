"""Coding challenge screen: problem scroll on the left, three play modes on the right."""
import threading

import pygame

from challenges.challenge_engine import MODES, RunReport
from game.scene import Scene
from settings import COLORS, SCREEN_H, SCREEN_W
from ui.background import JungleBackground
from ui.code_editor import CodeEditor, TextField
from ui.dialogue import wrap_text
from ui.widgets import Button, Fonts, draw_panel, draw_text

DIFF_COLOR = {"easy": (120, 226, 110), "medium": (255, 200, 80), "hard": (255, 110, 90)}
MODE_LABEL = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}
LEFT = pygame.Rect(10, 64, 410, 566)
RIGHT = pygame.Rect(430, 64, 520, 566)
ROW_Y = RIGHT.bottom - 56            # bottom button row
RESULT_H = 146


def fit_text(text: str, max_w: int, sizes=(34, 30, 26, 22, 18)) -> int:
    for size in sizes:
        if Fonts.get(size).size(text)[0] <= max_w:
            return size
    return sizes[-1]


class ChallengeScene(Scene):
    def __init__(self, game, question: dict):
        super().__init__(game)
        self.q = question
        self.engine = game.challenges
        self.bg = JungleBackground()
        self.t = 0.0
        progress = game.db.get_challenge_progress().get(question["id"], {})
        self.solved = {m: progress.get(m, False) for m in MODES}
        self.mode = "advanced" if self.solved["beginner"] and self.solved["intermediate"] else (
            "intermediate" if self.solved["beginner"] else "beginner")
        self.hints = 0
        self.scroll = 0
        self.running = False
        self._pending = None
        self.report: RunReport | None = None
        self.message = ""          # beginner feedback / reward banner
        self.message_color = COLORS["text"]
        self.choice = 0
        self.revealed = False
        self.field_i = 0
        self.back = Button("Back", (10, 10, 100, 42), self._close)
        self.tabs = [Button(MODE_LABEL[m], (528 + i * 138, 10, 134, 42), None) for i, m in enumerate(MODES)]
        self.btn_hint = Button("Hint", (RIGHT.x + 10, ROW_Y, 160, 44), self._hint)
        self.btn_run = Button("Run", (RIGHT.x + 180, ROW_Y, 160, 44), lambda: self._run(False))
        self.btn_submit = Button("Submit", (RIGHT.x + 350, ROW_Y, 160, 44), lambda: self._run(True))

        code_h = RIGHT.h - 40 - 60 - RESULT_H - 16
        self.editor = CodeEditor((RIGHT.x + 10, RIGHT.y + 40, RIGHT.w - 20, code_h),
                                 game.drafts.get((question["id"], "advanced"), question["starter"]))
        blanks = question["intermediate"]["blanks"]
        view_h = code_h - len(blanks) * 40 - 6
        self.view = CodeEditor((RIGHT.x + 10, RIGHT.y + 40, RIGHT.w - 20, view_h),
                               question["intermediate"]["template"], size=16, readonly=True)
        saved = game.drafts.get((question["id"], "intermediate"), [""] * len(blanks))
        self.fields = []
        for i in range(len(blanks)):
            f = TextField((RIGHT.x + 10, self.view.rect.bottom + 6 + i * 40, RIGHT.w - 20, 34), f"{i + 1}:")
            f.text, f.cursor = saved[i], len(saved[i])
            self.fields.append(f)
        self._build_left()
        pygame.key.start_text_input()

    # ---- left panel (problem statement) -----------------------------------------
    def _build_left(self) -> None:
        q, w = self.q, LEFT.w - 40
        surf = pygame.Surface((w, 2600), pygame.SRCALPHA)
        y = 0

        def para(text, size=23, color=COLORS["text"], indent=0, font=None):
            nonlocal y
            lines = wrap_text(text.replace("`", ""), size, w - indent) if font is None else [text]
            for line in lines:
                draw_text(surf, line, size, color, (indent, y))
                y += size + 4
            y += 4

        def heading(text):
            nonlocal y
            y += 6
            draw_text(surf, text, 28, COLORS["title"], (0, y))
            y += 32

        draw_text(surf, q["difficulty"].upper(), 24, DIFF_COLOR[q["difficulty"]], (0, y))
        draw_text(surf, "  |  ".join(q["topics"][:3]), 20, COLORS["text_dim"],
                  (Fonts.get(24).size(q["difficulty"].upper())[0] + 14, y + 3))
        y += 30
        para(f"Target: {q['complexity']}", 21, COLORS["xp_bar"])
        src = q["source"]
        if src["companies"]:
            para(f"Asked by {src['companies']} companies (LeetCode data)", 20, COLORS["text_dim"])
        para(q["description"])
        heading("Examples")
        for ex in q["examples"]:
            for label, value in (("Input", ex["input"]), ("Output", ex["output"])):
                for i, line in enumerate(wrap_text(f"{label}: {value}", 20, w - 8)):
                    draw_text(surf, line, 20, (190, 226, 170), (8, y))
                    y += 23
            if ex["note"]:
                para(ex["note"], 19, COLORS["text_dim"], 8)
            y += 4
        heading("Constraints")
        for c in q["constraints"]:
            para("- " + c, 21)
        heading(f"Hints ({self.hints}/{len(q['hints'])})")
        for i in range(self.hints):
            para(f"{i + 1}. {q['hints'][i]}", 22, (255, 226, 150))
        if self.hints == 0:
            para("Stuck? Press the Hint button.", 20, COLORS["text_dim"])
        self.left_h = y + 10
        self.left = surf
        self.scroll = min(self.scroll, max(0, self.left_h - (LEFT.h - 24)))

    # ---- actions ------------------------------------------------------------------------
    def _save_drafts(self) -> None:
        self.game.drafts[(self.q["id"], "advanced")] = self.editor.text
        self.game.drafts[(self.q["id"], "intermediate")] = [f.text for f in self.fields]

    def _close(self) -> None:
        self._save_drafts()
        pygame.key.stop_text_input()
        self.game.pop()

    def _set_mode(self, mode: str) -> None:
        if mode != self.mode and not self.running:
            self._save_drafts()
            self.mode, self.report, self.message, self.revealed = mode, None, "", False
            self.game.audio.play("select")

    def _hint(self) -> None:
        if self.hints < len(self.q["hints"]):
            self.hints += 1
            self.game.audio.play("select")
            self._build_left()
            self.scroll = max(0, self.left_h - (LEFT.h - 24))

    def _run(self, hidden: bool) -> None:
        """Beginner: check the chosen option. Other modes: grade code in the sandbox."""
        if self.running:
            return
        if self.mode == "beginner":
            if hidden:
                self._submit_choice()
            return
        if self.mode == "advanced":
            source, errors = self.editor.text, []
        else:
            source, errors = self.engine.build_fill_source(self.q, [f.text for f in self.fields])
        if errors:
            self.report, self.message = RunReport(errors=errors), ""
            return
        self.running, self.report, self.message = True, None, ""

        def job():
            try:
                rep = self.engine.run(self.q, source, include_hidden=hidden)
            except Exception as exc:  # never let a grader bug freeze the game
                rep = RunReport(errors=[f"Internal error: {exc}"])
            self._pending = (rep, hidden)

        threading.Thread(target=job, daemon=True).start()

    def _submit_choice(self) -> None:
        ok = self.engine.check_choice(self.q, self.choice)
        self.revealed = True
        if ok:
            self._award("beginner")
        else:
            self.game.db.record_challenge_result(self.q["id"], "beginner", False)
            self.message, self.message_color = "Not quite - read the explanation and try another option.", COLORS["warn"]

    def _award(self, mode: str) -> None:
        first = self.game.db.record_challenge_result(self.q["id"], mode, True)
        self.solved[mode] = True
        if first:
            r = self.engine.reward(self.q, mode)
            self.game.db.add_rewards(r["coins"], r["xp"])
            self.message = f"SOLVED!  +{r['xp']} XP   +{r['coins']} coins"
            self.game.audio.play("levelup")
        else:
            self.message = "Solved again - rewards are given once per mode."
            self.game.audio.play("chest")
        self.message_color = COLORS["title"]

    def _finish(self, report: RunReport, hidden: bool) -> None:
        self.report, self.running = report, False
        if report.errors:
            self.game.audio.play("back")
        elif hidden:
            if report.all_passed:
                self._award(self.mode)
            else:
                self.game.db.record_challenge_result(self.q["id"], self.mode, False)
                self.game.audio.play("back")
        else:
            self.game.audio.play("select" if report.all_passed else "back")

    # ---- events -------------------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.audio.play("back")
                return self._close()
            if event.key in (pygame.K_F1, pygame.K_F2, pygame.K_F3):
                return self._set_mode(MODES[event.key - pygame.K_F1])
            if event.key == pygame.K_F5 and self.mode != "beginner":
                return self._run(False)
            if event.key == pygame.K_F6:
                return self._run(True)
        if event.type == pygame.MOUSEWHEEL and LEFT.collidepoint(pygame.mouse.get_pos()):
            self.scroll = max(0, min(max(0, self.left_h - (LEFT.h - 24)), self.scroll - event.y * 40))
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back.rect.collidepoint(event.pos):
                self.game.audio.play("back")
                return self._close()
            for tab, mode in zip(self.tabs, MODES):
                if tab.rect.collidepoint(event.pos):
                    return self._set_mode(mode)
            for b in (self.btn_hint, self.btn_run, self.btn_submit):
                if b.enabled and b.rect.collidepoint(event.pos) and not (b is self.btn_run and self.mode == "beginner"):
                    return b.on_click()
        if self.running:
            return
        if self.mode == "advanced":
            self.editor.handle_event(event)
        elif self.mode == "intermediate":
            self._fields_event(event)
        else:
            self._choice_event(event)

    def _fields_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, f in enumerate(self.fields):
                if f.rect.collidepoint(event.pos):
                    self.field_i = i
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_TAB, pygame.K_RETURN):
            step = -1 if event.mod & pygame.KMOD_SHIFT else 1
            self.field_i = (self.field_i + step) % len(self.fields)
        elif event.type == pygame.MOUSEWHEEL:
            self.view.handle_event(event)
        else:
            self.fields[self.field_i].handle_event(event)

    def _option_rects(self):
        rects, y = [], RIGHT.y + 40 + len(wrap_text(self.q["beginner"]["prompt"], 28, RIGHT.w - 40)) * 32 + 14
        for opt in self.q["beginner"]["options"]:
            h = len(wrap_text(opt, 23, RIGHT.w - 90)) * 26 + 20
            rects.append(pygame.Rect(RIGHT.x + 14, y, RIGHT.w - 28, h))
            y += h + 10
        return rects

    def _choice_event(self, event):
        n = len(self.q["beginner"]["options"])
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self._option_rects()):
                if r.collidepoint(event.pos):
                    self.choice, self.revealed = i, False
                    self.game.audio.play("move")
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_1 + n - 1:
                self.choice, self.revealed = event.key - pygame.K_1, False
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.choice, self.revealed = (self.choice - 1) % n, False
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.choice, self.revealed = (self.choice + 1) % n, False
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._submit_choice()

    # ---- loop --------------------------------------------------------------------------------------
    def update(self, dt):
        self.t += dt
        if self._pending:
            report, hidden = self._pending
            self._pending = None
            self._finish(report, hidden)

    def draw(self, screen):
        self.bg.draw(screen, self.t)
        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((4, 16, 10, 150))
        screen.blit(dim, (0, 0))
        self._draw_top(screen)
        draw_panel(screen, LEFT, fill=(34, 30, 20), vines=False)
        clip = screen.get_clip()
        screen.set_clip(LEFT.inflate(-26, -26))
        screen.blit(self.left, (LEFT.x + 20, LEFT.y + 14), pygame.Rect(0, self.scroll, LEFT.w - 40, LEFT.h - 28))
        screen.set_clip(clip)
        if self.left_h > LEFT.h - 24:  # scrollbar
            track = pygame.Rect(LEFT.right - 16, LEFT.y + 14, 5, LEFT.h - 28)
            pygame.draw.rect(screen, (20, 16, 10), track)
            ratio = (LEFT.h - 24) / self.left_h
            top = track.y + (track.h - track.h * ratio) * self.scroll / max(1, self.left_h - (LEFT.h - 24))
            pygame.draw.rect(screen, COLORS["panel_edge"], (track.x, top, 5, track.h * ratio))
        draw_panel(screen, RIGHT, vines=False)
        {"beginner": self._draw_beginner, "intermediate": self._draw_fill,
         "advanced": self._draw_advanced}[self.mode](screen)
        self._draw_buttons(screen)
        if self.mode != "beginner":
            self._draw_results(screen)

    def _draw_top(self, screen):
        self.back.draw(screen, False)
        size = fit_text(self.q["title"], 385)
        draw_text(screen, self.q["title"], size, COLORS["title"], (125, 31), "midleft", shadow=True)
        for tab, mode in zip(self.tabs, MODES):
            tab.draw(screen, mode == self.mode)
            if self.solved[mode]:  # green gem marks a solved mode
                pygame.draw.polygon(screen, (120, 240, 120), [(tab.rect.right - 14, tab.rect.y + 4),
                                    (tab.rect.right - 6, tab.rect.y + 12), (tab.rect.right - 14, tab.rect.y + 20),
                                    (tab.rect.right - 22, tab.rect.y + 12)])

    def _draw_buttons(self, screen):
        self.btn_hint.label = f"Hint ({self.hints}/{len(self.q['hints'])})"
        self.btn_hint.enabled = self.hints < len(self.q["hints"])
        self.btn_submit.enabled = not self.running
        self.btn_run.enabled = not self.running
        self.btn_hint.draw(screen, False)
        if self.mode != "beginner":
            self.btn_run.draw(screen, False)
        self.btn_submit.draw(screen, False)

    def _draw_beginner(self, screen):
        b = self.q["beginner"]
        draw_text(screen, "Choose the best answer", 22, COLORS["text_dim"], (RIGHT.x + 20, RIGHT.y + 14))
        y = RIGHT.y + 40
        for line in wrap_text(b["prompt"], 28, RIGHT.w - 40):
            draw_text(screen, line, 28, COLORS["text"], (RIGHT.x + 20, y))
            y += 32
        for i, (rect, opt) in enumerate(zip(self._option_rects(), b["options"])):
            picked = i == self.choice
            border = COLORS["btn_focus"] if picked else COLORS["border"]
            fill = (60, 48, 28) if picked else (30, 40, 30)
            if self.revealed:
                if i == b["answer"]:
                    border, fill = (120, 240, 120), (28, 70, 34)
                elif picked:
                    border, fill = (255, 110, 90), (80, 30, 26)
            pygame.draw.rect(screen, border, rect)
            pygame.draw.rect(screen, fill, rect.inflate(-4, -4))
            draw_text(screen, "ABCD"[i], 30, COLORS["title"], (rect.x + 14, rect.centery), "midleft")
            for k, line in enumerate(wrap_text(opt, 23, RIGHT.w - 90)):
                draw_text(screen, line, 23, COLORS["text"], (rect.x + 48, rect.y + 10 + k * 26))
        end_y = self._option_rects()[-1].bottom + 14
        if self.message:
            draw_text(screen, self.message, 28, self.message_color, (RIGHT.x + 20, end_y))
            end_y += 34
        if self.revealed:
            for line in wrap_text(b["explanation"], 21, RIGHT.w - 40):
                draw_text(screen, line, 21, COLORS["xp_bar"], (RIGHT.x + 20, end_y))
                end_y += 24
        else:
            draw_text(screen, "Pick with the mouse, 1-4 or arrows. Enter submits.", 19, COLORS["text_dim"],
                      (RIGHT.x + 20, ROW_Y - 28))

    def _draw_fill(self, screen):
        draw_text(screen, "Complete the missing code", 22, COLORS["text_dim"], (RIGHT.x + 20, RIGHT.y + 14))
        draw_text(screen, "Tab: next blank   F5 Run   F6 Submit", 17, COLORS["text_dim"],
                  (RIGHT.right - 20, RIGHT.y + 16), "topright")
        display = []
        for line in self.view.lines:
            for i, f in enumerate(self.fields, 1):
                line = line.replace(f"@@{i}@@", f.text if f.text else f"__{i}__")
            display.append(line)
        self.view.draw(screen, False, self.t, display_lines=display)
        for i, f in enumerate(self.fields):
            f.draw(screen, i == self.field_i and not self.running, self.t)

    def _draw_advanced(self, screen):
        draw_text(screen, "Write your solution", 22, COLORS["text_dim"], (RIGHT.x + 20, RIGHT.y + 14))
        draw_text(screen, "F5 Run samples   F6 Submit", 17, COLORS["text_dim"],
                  (RIGHT.right - 20, RIGHT.y + 16), "topright")
        self.editor.draw(screen, not self.running, self.t)

    def _draw_results(self, screen):
        box = pygame.Rect(RIGHT.x + 10, ROW_Y - RESULT_H - 8, RIGHT.w - 20, RESULT_H)
        pygame.draw.rect(screen, COLORS["border"], box)
        pygame.draw.rect(screen, (14, 22, 16), box.inflate(-4, -4))
        x, y = box.x + 12, box.y + 8
        if self.running:
            dots = "." * (int(self.t * 3) % 4)
            return draw_text(screen, f"Running tests in the sandbox{dots}", 26, COLORS["title"], (x, y))
        if self.message:
            draw_text(screen, self.message, 28, self.message_color, (x, y))
            y += 30
        rep = self.report
        if rep is None:
            if not self.message:
                draw_text(screen, "Run checks the sample tests. Submit also runs hidden tests.", 20,
                          COLORS["text_dim"], (x, y))
            return
        if rep.errors:
            for e in rep.errors[:4]:
                for line in wrap_text(e, 20, box.w - 24)[:2]:
                    draw_text(screen, line, 20, COLORS["warn"], (x, y))
                    y += 22
            return
        color = COLORS["xp_bar"] if rep.all_passed else COLORS["warn"]
        draw_text(screen, f"Passed {rep.passed}/{rep.total} tests", 26, color, (x, y))
        y += 28
        fail = next((c for c in rep.cases if not c.passed), None)
        if fail:
            draw_text(screen, f"{fail.label}: {fail.status.upper()}", 20, COLORS["warn"], (x, y))
            y += 22
            for raw in fail.detail.split("\n"):
                for line in wrap_text(raw, 19, box.w - 24)[:2]:
                    if y < box.bottom - 18:
                        draw_text(screen, line, 19, COLORS["text"], (x, y))
                        y += 20
