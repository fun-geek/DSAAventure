"""Small multi-line code editor and single-line text field for pygame."""
import keyword
import re

import pygame

from ui.widgets import Fonts

KEYWORDS = set(keyword.kwlist) - {"True", "False", "None"}
TOKEN = re.compile(r"(#.*$)|(\"[^\"]*\"|'[^']*')|\b(\d+)\b|\b([A-Za-z_]\w*)\b")
C_TEXT, C_KW, C_STR = (230, 226, 200), (255, 150, 80), (160, 224, 110)
C_COMMENT, C_NUM, C_NAME, C_BUILTIN = (110, 150, 110), (120, 206, 236), (255, 208, 84), (180, 160, 240)
BUILTINS = {"True", "False", "None", "self", "len", "range", "enumerate", "min", "max", "sum",
            "sorted", "set", "dict", "list", "int", "float", "str", "zip", "abs", "print"}


def highlight(line: str) -> list[tuple[str, tuple]]:
    """Split a line into (text, colour) segments for simple Python highlighting."""
    segs, pos = [], 0
    for m in TOKEN.finditer(line):
        if m.start() > pos:
            segs.append((line[pos:m.start()], C_TEXT))
        text = m.group(0)
        if m.group(1):
            col = C_COMMENT
        elif m.group(2):
            col = C_STR
        elif m.group(3):
            col = C_NUM
        elif text in KEYWORDS:
            col = C_KW
        elif text in BUILTINS:
            col = C_BUILTIN
        elif line[:m.start()].rstrip().endswith(("def", "class")):
            col = C_NAME
        else:
            col = C_TEXT
        segs.append((text, col))
        pos = m.end()
    if pos < len(line):
        segs.append((line[pos:], C_TEXT))
    return segs


def _paste() -> str:
    try:
        pygame.scrap.init()
        data = pygame.scrap.get(pygame.SCRAP_TEXT)
        return data.decode("utf-8", "ignore").replace("\x00", "").replace("\r\n", "\n") if data else ""
    except Exception:
        return ""


class CodeEditor:
    TAB = "    "
    MAX_LINES = 250

    def __init__(self, rect, text: str = "", size: int = 17, readonly: bool = False):
        self.rect = pygame.Rect(rect)
        self.font = Fonts.mono(size)
        self.lh = self.font.get_linesize() + 2
        self.readonly = readonly
        self.set_text(text)
        self.gutter = 38

    # ---- content ------------------------------------------------------------
    def set_text(self, text: str) -> None:
        self.lines = text.split("\n") or [""]
        self.row = self.col = self.top = 0

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    @property
    def visible_rows(self) -> int:
        return max(1, (self.rect.h - 8) // self.lh)

    # ---- editing ---------------------------------------------------------------
    def _insert(self, text: str) -> None:
        for ch in text:
            if ch == "\n":
                if len(self.lines) >= self.MAX_LINES:
                    return
                line = self.lines[self.row]
                indent = re.match(r" *", line[:self.col]).group(0)
                if line[:self.col].rstrip().endswith(":"):
                    indent += self.TAB
                self.lines[self.row:self.row + 1] = [line[:self.col], indent + line[self.col:]]
                self.row, self.col = self.row + 1, len(indent)
            elif ch == "\t":
                self._insert(self.TAB)
            elif ch.isprintable():
                line = self.lines[self.row]
                if len(line) < 160:
                    self.lines[self.row] = line[:self.col] + ch + line[self.col:]
                    self.col += 1
        self._scroll_to_cursor()

    def _backspace(self) -> None:
        line = self.lines[self.row]
        if self.col > 0:
            n = 4 if line[:self.col].strip() == "" and self.col % 4 == 0 else 1  # dedent whole tab
            self.lines[self.row] = line[:self.col - n] + line[self.col:]
            self.col -= n
        elif self.row > 0:
            prev = self.lines[self.row - 1]
            self.lines[self.row - 1:self.row + 1] = [prev + line]
            self.row, self.col = self.row - 1, len(prev)

    def _delete(self) -> None:
        line = self.lines[self.row]
        if self.col < len(line):
            self.lines[self.row] = line[:self.col] + line[self.col + 1:]
        elif self.row + 1 < len(self.lines):
            self.lines[self.row:self.row + 2] = [line + self.lines[self.row + 1]]

    def _scroll_to_cursor(self) -> None:
        if self.row < self.top:
            self.top = self.row
        elif self.row >= self.top + self.visible_rows:
            self.top = self.row - self.visible_rows + 1

    def _move(self, drow: int, dcol: int) -> None:
        if dcol:
            self.col += dcol
            if self.col < 0 and self.row > 0:
                self.row, self.col = self.row - 1, len(self.lines[self.row - 1])
            elif self.col > len(self.lines[self.row]) and self.row + 1 < len(self.lines):
                self.row, self.col = self.row + 1, 0
        if drow:
            self.row = max(0, min(len(self.lines) - 1, self.row + drow))
        self.col = max(0, min(self.col, len(self.lines[self.row])))
        self._scroll_to_cursor()

    # ---- events -------------------------------------------------------------------
    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            self.top = max(0, min(max(0, len(self.lines) - self.visible_rows), self.top - event.y * 3))
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            if not self.readonly:
                self.row = max(0, min(len(self.lines) - 1, self.top + (event.pos[1] - self.rect.y - 4) // self.lh))
                x = event.pos[0] - self.rect.x - self.gutter - 6
                line = self.lines[self.row]
                self.col = min(range(len(line) + 1), key=lambda c: abs(self.font.size(line[:c])[0] - x))
            return True
        if self.readonly:
            return False
        if event.type == pygame.TEXTINPUT:
            self._insert(event.text)
            return True
        if event.type == pygame.KEYDOWN:
            k = event.key
            if event.mod & pygame.KMOD_CTRL:
                if k == pygame.K_v:
                    self._insert(_paste())
                    return True
                return False
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._insert("\n")
            elif k == pygame.K_TAB:
                self._insert(self.TAB)
            elif k == pygame.K_BACKSPACE:
                self._backspace()
            elif k == pygame.K_DELETE:
                self._delete()
            elif k == pygame.K_LEFT:
                self._move(0, -1)
            elif k == pygame.K_RIGHT:
                self._move(0, 1)
            elif k == pygame.K_UP:
                self._move(-1, 0)
            elif k == pygame.K_DOWN:
                self._move(1, 0)
            elif k == pygame.K_HOME:
                self.col = len(self.lines[self.row]) - len(self.lines[self.row].lstrip())
            elif k == pygame.K_END:
                self.col = len(self.lines[self.row])
            elif k == pygame.K_PAGEUP:
                self._move(-self.visible_rows, 0)
            elif k == pygame.K_PAGEDOWN:
                self._move(self.visible_rows, 0)
            else:
                return False
            return True
        return False

    # ---- drawing -------------------------------------------------------------------
    def draw(self, screen, focused: bool = True, t: float = 0.0, display_lines=None) -> None:
        pygame.draw.rect(screen, (8, 14, 10), self.rect)
        pygame.draw.rect(screen, (112, 190, 90) if focused else (80, 96, 70), self.rect, 2)
        pygame.draw.rect(screen, (16, 26, 18), (self.rect.x + 2, self.rect.y + 2, self.gutter, self.rect.h - 4))
        lines = display_lines if display_lines is not None else self.lines
        clip = screen.get_clip()
        screen.set_clip(self.rect.inflate(-4, -4))
        for i in range(self.top, min(len(lines), self.top + self.visible_rows)):
            y = self.rect.y + 4 + (i - self.top) * self.lh
            num = self.font.render(str(i + 1), True, (96, 130, 96))
            screen.blit(num, (self.rect.x + self.gutter - num.get_width() + 2, y))
            x = self.rect.x + self.gutter + 8
            for text, color in highlight(lines[i]):
                img = self.font.render(text, True, color)
                screen.blit(img, (x, y))
                x += img.get_width()
        if focused and not self.readonly and int(t * 2) % 2 == 0:
            line = self.lines[self.row]
            cx = self.rect.x + self.gutter + 8 + self.font.size(line[:self.col])[0]
            cy = self.rect.y + 4 + (self.row - self.top) * self.lh
            pygame.draw.rect(screen, (255, 230, 120), (cx, cy, 2, self.lh - 2))
        screen.set_clip(clip)


class TextField:
    """Single-line input used for fill-in-the-blank answers."""

    def __init__(self, rect, label: str = "", max_len: int = 100):
        self.rect = pygame.Rect(rect)
        self.label, self.max_len = label, max_len
        self.text, self.cursor = "", 0
        self.font = Fonts.mono(17)

    def handle_event(self, event) -> bool:
        if event.type == pygame.TEXTINPUT:
            if len(self.text) < self.max_len and event.text.isprintable():
                self.text = self.text[:self.cursor] + event.text + self.text[self.cursor:]
                self.cursor += len(event.text)
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE and self.cursor:
                self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
                self.cursor -= 1
            elif event.key == pygame.K_DELETE:
                self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]
            elif event.key == pygame.K_LEFT:
                self.cursor = max(0, self.cursor - 1)
            elif event.key == pygame.K_RIGHT:
                self.cursor = min(len(self.text), self.cursor + 1)
            elif event.key == pygame.K_HOME:
                self.cursor = 0
            elif event.key == pygame.K_END:
                self.cursor = len(self.text)
            elif event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
                chunk = _paste().replace("\n", " ")[:self.max_len]
                self.text = (self.text[:self.cursor] + chunk + self.text[self.cursor:])[:self.max_len]
                self.cursor += len(chunk)
            else:
                return False
            return True
        return False

    def draw(self, screen, focused: bool, t: float) -> None:
        pygame.draw.rect(screen, (8, 14, 10), self.rect)
        pygame.draw.rect(screen, (255, 208, 84) if focused else (80, 96, 70), self.rect, 2)
        label = Fonts.get(22).render(self.label, True, (255, 208, 84))
        screen.blit(label, (self.rect.x + 8, self.rect.centery - label.get_height() // 2))
        x0 = self.rect.x + 14 + label.get_width()
        clip = screen.get_clip()
        screen.set_clip(self.rect.inflate(-4, -4))
        x = x0
        for text, color in highlight(self.text):
            img = self.font.render(text, True, color)
            screen.blit(img, (x, self.rect.centery - img.get_height() // 2))
            x += img.get_width()
        if focused and int(t * 2) % 2 == 0:
            cx = x0 + self.font.size(self.text[:self.cursor])[0]
            pygame.draw.rect(screen, (255, 230, 120), (cx, self.rect.y + 6, 2, self.rect.h - 12))
        screen.set_clip(clip)
