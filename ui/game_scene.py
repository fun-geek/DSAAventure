"""Exploration scene: depth-sorted world, objects, interaction, dialogue, HUD."""
import pygame

from game.camera import Camera
import math
import random

from game.objects import Totem, make_object
from game.player import Player
from game.scene import Scene
from game.world import World
from systems.quest_manager import QuestManager
from ui.quest_log import draw_quest_log, draw_quest_tracker
from settings import COLORS, INTERACT_RANGE, SCREEN_H, SCREEN_W, WORLDS
from systems.progression import level_from_xp
from ui.challenge_screen import ChallengeScene
from ui.dialogue import DialogueBox
from ui.hud import draw_hud
from ui.widgets import Button, ButtonGroup, Fonts, draw_panel, draw_text
from worlds import WORLD_MAPS

INTERACT_KEYS = (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)


class GameScene(Scene):
    def __init__(self, game, world_id: int):
        super().__init__(game)
        build, spawn, object_defs, quest_defs = WORLD_MAPS[world_id]
        self.world_id = world_id
        self.info = next(w for w in WORLDS if w["id"] == world_id)
        self.world = World(build(), spawn)
        self.player = Player(spawn)
        self.camera = Camera((SCREEN_W, SCREEN_H), self.world.pixel_size)
        self.camera.snap(self.player.center)
        self.save = game.db.get_player()
        self.dialogue = DialogueBox()
        self.floaters: list[list] = []  # [text, world_x, world_y, life, color]
        self.t = 0.0
        self.paused = False

        self.collected = game.db.get_collected(world_id)
        self.qm = QuestManager(game.db, quest_defs)
        self.show_log = False
        saved = self.collected
        self.objects = [make_object(d) for d in object_defs]
        for obj in self.objects:
            if obj.persistent and obj.id in saved:
                obj.restore()
            if obj.solid:
                self.world.blockers.add((obj.tx, obj.ty))

        self._sync_solved()
        self.vignette = self._make_vignette()
        rng = random.Random(5)  # drifting pollen / fireflies for atmosphere
        self.motes = [[rng.uniform(0, SCREEN_W), rng.uniform(0, SCREEN_H), rng.uniform(0, 6.28),
                       rng.uniform(8, 22)] for _ in range(36)]
        x = (SCREEN_W - 320) // 2
        self.pause_group = ButtonGroup([
            Button("Resume", (x, 280, 320, 46), self._resume),
            Button("Back to World Select", (x, 340, 320, 46), self.game.pop)], game.audio)

    @staticmethod
    def _make_vignette() -> pygame.Surface:
        """Soft green-black edge darkening plus a faint canopy tint."""
        small = pygame.Surface((48, 32), pygame.SRCALPHA)
        for y in range(32):
            for x in range(48):
                d = math.hypot((x - 23.5) / 24, (y - 15.5) / 16)
                small.set_at((x, y), (4, 20, 10, int(max(0, min(1, (d - 0.55) / 0.75)) * 150) + 14))
        return pygame.transform.smoothscale(small, (SCREEN_W, SCREEN_H))

    def _sync_solved(self) -> None:
        """Mirror solved puzzles into quest progress and totem colours."""
        solved = self.game.db.solved_questions()
        self.collected |= {f"solve_{q}" for q in solved}
        for o in self.objects:
            if isinstance(o, Totem):
                o.solved = o.qid in solved

    def open_challenge(self, qid: str) -> None:
        self.game.push(ChallengeScene(self.game, self.game.challenges.bank.get(qid)))

    # ---- API used by objects ---------------------------------------------
    def say(self, speaker: str, text: str) -> None:
        self.dialogue.show(speaker, text)

    def play(self, name: str) -> None:
        self.game.audio.play(name)

    def mark(self, obj) -> None:
        self.collected.add(obj.id)
        self.game.db.mark_collected(self.world_id, obj.id)

    # ---- NPCs and quests ---------------------------------------------------
    def talk_to(self, npc) -> None:
        npc.face_towards(self.player.center)
        q = self.qm.quest_for_npc(npc.id)
        status = self.qm.status(q["id"], self.collected) if q else None
        if status == "available":
            self.dialogue.show_lines(npc.name, q["offer"], on_close=lambda: self._accept(q))
        elif status == "active":
            cur, target = self.qm.progress(q, self.collected)
            self.dialogue.show_lines(npc.name, q["progress"] + [f"({cur}/{target} so far.)"])
        elif status == "ready":
            self.dialogue.show_lines(npc.name, q["complete"], on_close=lambda: self._complete(q))
        else:
            self.dialogue.show(npc.name, npc.next_idle())

    def _accept(self, q) -> None:
        if self.qm.accept(q["id"], self.collected):
            self.play("select")
            self.floaters.append([f"New quest: {q['title']}", self.player.center.x,
                                  self.player.center.y - 40, 2.5, (255, 255, 255)])

    def _complete(self, q) -> None:
        reward = self.qm.complete(q["id"], self.collected)
        if reward:
            self.play("chest")
            self.floaters.append(["Quest complete!", self.player.center.x,
                                  self.player.center.y - 70, 2.5, (255, 255, 255)])
            self.grant(reward["coins"], reward["xp"], self.player.center)

    def _marker(self, npc):
        q = self.qm.quest_for_npc(npc.id)
        status = self.qm.status(q["id"], self.collected) if q else None
        return {"available": ("!", COLORS["title"]), "ready": ("?", COLORS["xp_bar"]),
                "active": ("...", COLORS["text_dim"])}.get(status)

    def grant(self, coins: int, xp: int, pos, quiet_sound: bool = False) -> None:
        old_level = level_from_xp(self.save["xp"])
        self.game.db.add_rewards(coins, xp)
        self.save = self.game.db.get_player()
        x, y = pos
        if coins:
            self.floaters.append([f"+{coins} coin{'s' if coins > 1 else ''}", x, y, 1.4, (255, 214, 102)])
        if xp:
            self.floaters.append([f"+{xp} XP", x, y - 22, 1.4, COLORS["xp_bar"]])
        if level_from_xp(self.save["xp"]) > old_level:
            self.floaters.append(["LEVEL UP!", self.player.center.x, self.player.center.y - 50, 2.2,
                                  (255, 255, 255)])
            self.play("levelup")

    # ---- interaction -------------------------------------------------------
    def _target(self):
        c, best, best_d = self.player.center, None, INTERACT_RANGE
        for o in self.objects:
            if o.interactive and not o.done:
                d = c.distance_to(o.rect.center)
                if d < best_d:
                    best, best_d = o, d
        return best

    def _resume(self):
        self.paused = False

    def handle_event(self, event):
        if self.show_log:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
                self.show_log = False
                self.game.audio.play("back")
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.audio.play("back")
            self.paused = not self.paused
        elif (event.type == pygame.KEYDOWN and event.key == pygame.K_q and not self.paused
              and not self.dialogue.active):
            self.show_log = True
            self.game.audio.play("select")
        elif self.paused:
            self.pause_group.handle_event(event)
        elif self.dialogue.active:
            if (event.type == pygame.KEYDOWN and event.key in INTERACT_KEYS) or (
                    event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.dialogue.advance()
        elif event.type == pygame.KEYDOWN and event.key in INTERACT_KEYS:
            target = self._target()
            if target:
                target.interact(self)

    # ---- loop ----------------------------------------------------------------
    def update(self, dt):
        if self.paused or self.show_log:
            return
        dt = min(dt, 0.05)
        self.t += dt
        if self.dialogue.update(dt):
            self.play("talk")
        direction = pygame.Vector2()
        if not self.dialogue.active:
            k = pygame.key.get_pressed()
            direction.update(
                (k[pygame.K_d] or k[pygame.K_RIGHT]) - (k[pygame.K_a] or k[pygame.K_LEFT]),
                (k[pygame.K_s] or k[pygame.K_DOWN]) - (k[pygame.K_w] or k[pygame.K_UP]))
            running = k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT]
        else:
            running = False
        self.player.update(dt, direction, running, self.world)
        self.camera.follow(self.player.center, dt)

        for o in self.objects:  # villagers turn to face a nearby player
            if hasattr(o, "face_towards"):
                near = self.player.center.distance_to(o.rect.center) < 150
                o.face_towards(self.player.center) if near else setattr(o, "facing", "down")
        hitbox = self.player.hitbox
        for o in self.objects:  # auto-collect pickups on contact
            if hasattr(o, "collect") and not o.done and hitbox.colliderect(o.rect.inflate(-6, -6)):
                o.collect(self)
        for m in self.motes:
            m[0] = (m[0] + math.sin(self.t * 0.6 + m[2]) * 10 * dt + 6 * dt) % SCREEN_W
            m[1] = (m[1] - m[3] * dt) % SCREEN_H
        for f in self.floaters:
            f[2] -= 30 * dt
            f[3] -= dt
        self.floaters = [f for f in self.floaters if f[3] > 0]

    def on_resume(self):
        self.save = self.game.db.get_player()
        self._sync_solved()

    def draw(self, screen):
        cx, cy = round(self.camera.pos.x), round(self.camera.pos.y)
        self.world.draw(screen, cx, cy, self.t)
        view = pygame.Rect(cx, cy, SCREEN_W, SCREEN_H).inflate(96, 96)
        items = list(self.world.visible_trees(cx, cy, SCREEN_W, SCREEN_H))
        for o in self.objects:
            if view.colliderect(o.rect) and not (hasattr(o, "collect") and o.done):
                sprite, pos = o.draw_item(self.t)
                items.append((o.sort_y, sprite, pos))
        items.append((self.player.hitbox.bottom, None, None))
        items.sort(key=lambda i: i[0])  # depth sort: lower on screen draws later
        for _, sprite, pos in items:
            if sprite is None:
                self.player.draw(screen, self.camera)
            else:
                screen.blit(sprite, (pos[0] - cx, pos[1] - cy))

        screen.blit(self.vignette, (0, 0))
        for mx, my, phase, _ in self.motes:  # glowing spores
            glow = (math.sin(self.t * 2 + phase) + 1) / 2
            if glow > 0.25:
                c = (int(190 + 60 * glow), 255, int(110 * glow))
                screen.fill(c, (int(mx), int(my), 3, 3))
        for text, x, y, life, color in self.floaters:
            draw_text(screen, text, 26, color, (x - cx, y - cy), "center", shadow=True)
        for o in self.objects:  # quest markers above villagers
            if hasattr(o, "face_towards") and view.colliderect(o.rect):
                marker = self._marker(o)
                if marker:
                    bob = round(abs(pygame.math.Vector2(0, 1).rotate(self.t * 200).y) * 4)
                    draw_text(screen, marker[0], 36, marker[1],
                              (o.rect.centerx - cx, o.rect.top - cy - 14 - bob), "center", shadow=True)
        target = None if self.dialogue.active or self.paused or self.show_log else self._target()
        if target:
            font_w = Fonts.get(22).size(target.prompt)[0]
            box = pygame.Rect(0, 0, font_w + 18, 26)
            lift = 52 if hasattr(target, "face_towards") else 22  # clear the quest marker
            box.center = (target.rect.centerx - cx, target.rect.top - cy - lift)
            pygame.draw.rect(screen, COLORS["border"], box.inflate(4, 4))
            pygame.draw.rect(screen, COLORS["panel"], box)
            draw_text(screen, target.prompt, 22, COLORS["title"], box.center, "center")

        draw_hud(screen, self.save, self.info["name"])
        draw_quest_tracker(screen, self.qm, self.collected)
        self.dialogue.draw(screen)
        if self.show_log:
            draw_quest_log(screen, self.qm, self.collected)
        if not self.paused and not self.dialogue.active and self.t < 6:
            draw_text(screen, "WASD / Arrows: move   Shift: run   E: interact   Q: quests   Esc: pause", 22,
                      COLORS["text"], (SCREEN_W // 2, SCREEN_H - 28), "center", shadow=True)
        if self.paused:
            dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            dim.fill((10, 6, 24, 150))
            screen.blit(dim, (0, 0))
            panel = pygame.Rect(0, 0, 440, 250)
            panel.center = (SCREEN_W // 2, 320)
            draw_panel(screen, panel)
            draw_text(screen, "PAUSED", 52, COLORS["title"], (panel.centerx, panel.y + 40), "center")
            self.pause_group.draw(screen)
