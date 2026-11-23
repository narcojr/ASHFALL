"""
states.py
---------
A small state machine: MenuState -> PlayingState -> (PauseState / GameOverState),
with a LevelTransitionState flashing between levels. Each state implements
handle_event(event), update(dt_ms), and draw(surface). Add a new screen by
subclassing GameState and calling manager.set_state(YourState(...)).

Infinite level progression lives here: PlayingState tracks a `level_number`
that starts at 1 (the hand-crafted intro) and increments forever - each
new level is built by level_generator.generate(), which makes it both
harder and different from the last (see level_generator.py / data.py).
"""

import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG_TOP, COLOR_BG_BOTTOM,
    COLOR_WHITE, COLOR_RED, COLOR_GOLD, KEY_PAUSE,
)
from src.player import Player
from src.level import Level
from src.camera import Camera
from src.ui import HUD
from src.data import INTRO_LEVEL_LAYOUT
from src import level_generator


def draw_vertical_gradient(surface, top_color, bottom_color):
    h = surface.get_height()
    for y in range(h):
        t = y / h
        color = tuple(int(top_color[i] + (bottom_color[i] - top_color[i]) * t) for i in range(3))
        pygame.draw.line(surface, color, (0, y), (surface.get_width(), y))


def build_layout(level_number):
    if level_number == 1:
        return INTRO_LEVEL_LAYOUT
    return level_generator.generate(level_number)


class GameState:
    def __init__(self, manager):
        self.manager = manager

    def handle_event(self, event):
        pass

    def update(self, dt_ms):
        pass

    def draw(self, surface):
        pass


class StateManager:
    def __init__(self):
        self.state = None

    def set_state(self, state):
        self.state = state

    def handle_event(self, event):
        self.state.handle_event(event)

    def update(self, dt_ms):
        self.state.update(dt_ms)

    def draw(self, surface):
        self.state.draw(surface)


# ---------------------------------------------------------------- MENU
class MenuState(GameState):
    def __init__(self, manager):
        super().__init__(manager)
        self.title_font = pygame.font.SysFont("georgia", 64, bold=True)
        self.sub_font = pygame.font.SysFont("consolas", 22)
        self.hint_font = pygame.font.SysFont("consolas", 18)
        self._t = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.manager.set_state(PlayingState(self.manager))

    def update(self, dt_ms):
        self._t += dt_ms

    def draw(self, surface):
        draw_vertical_gradient(surface, (5, 5, 10), COLOR_BG_BOTTOM)

        title = self.title_font.render("ASHFALL", True, COLOR_RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        surface.blit(title, title_rect)

        subtitle = self.sub_font.render("RISE FROM THE ASHES", True, COLOR_GOLD)
        sub_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 210))
        surface.blit(subtitle, sub_rect)

        blink = (self._t // 500) % 2 == 0
        if blink:
            hint = self.hint_font.render("Press ENTER to begin your exile's return", True, COLOR_WHITE)
            hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, 320))
            surface.blit(hint, hint_rect)

        controls = [
            "A/D or Arrows - Move      SPACE/W - Jump",
            "J or ENTER - Attack       E - Interact (open chest)",
            "Levels regenerate forever and get harder each time.",
            "ESC - Pause",
        ]
        for i, line in enumerate(controls):
            c = self.hint_font.render(line, True, (170, 170, 180))
            surface.blit(c, c.get_rect(center=(SCREEN_WIDTH // 2, 400 + i * 24)))


# ---------------------------------------------------------------- PLAYING
class PlayingState(GameState):
    def __init__(self, manager, player=None, level_number=1):
        super().__init__(manager)
        self.player = player if player is not None else Player()
        self.level_number = level_number
        self.level = Level(build_layout(level_number), self.player)
        self.camera = Camera(self.level.width_px)
        self.hud = HUD()
        self._interact_pressed = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in KEY_PAUSE:
                self.manager.set_state(PauseState(self.manager, self))
            if event.key == pygame.K_e:
                self._interact_pressed = True

    def update(self, dt_ms):
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys, dt_ms)
        self.player.update(dt_ms, self.level.platforms)

        self.level.update(dt_ms, self._interact_pressed)
        self._interact_pressed = False

        self.camera.update(self.player.rect)

        if not self.player.alive:
            self.manager.set_state(GameOverState(self.manager, self.level_number, self.player.pixel_core_count))
        elif self.level.level_complete:
            self.manager.set_state(
                LevelTransitionState(self.manager, self.player, self.level_number + 1)
            )

    def draw(self, surface):
        draw_vertical_gradient(surface, COLOR_BG_TOP, COLOR_BG_BOTTOM)
        self.level.draw_background(surface, self.camera)
        self.level.draw_objects(surface, self.camera)
        self.player.draw(surface, self.camera)
        self.hud.draw(surface, self.player, level_number=self.level_number, biome_name=self.level.theme_name)


# ---------------------------------------------------------------- LEVEL TRANSITION
class LevelTransitionState(GameState):
    """A short banner between levels, then hands off to a freshly generated one."""

    DURATION_MS = 1300

    def __init__(self, manager, player, next_level_number):
        super().__init__(manager)
        self.player = player
        self.next_level_number = next_level_number
        self.timer_ms = 0
        self.font = pygame.font.SysFont("georgia", 46, bold=True)
        self.sub_font = pygame.font.SysFont("consolas", 18)

    def update(self, dt_ms):
        self.timer_ms += dt_ms
        if self.timer_ms >= self.DURATION_MS:
            self.manager.set_state(
                PlayingState(self.manager, player=self.player, level_number=self.next_level_number)
            )

    def draw(self, surface):
        draw_vertical_gradient(surface, (10, 8, 14), (40, 20, 30))
        text = self.font.render(f"LEVEL {self.next_level_number}", True, COLOR_GOLD)
        surface.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10)))
        sub = self.sub_font.render("The wasteland shifts ahead...", True, COLOR_WHITE)
        surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)))


# ---------------------------------------------------------------- PAUSE
class PauseState(GameState):
    def __init__(self, manager, playing_state):
        super().__init__(manager)
        self.playing_state = playing_state
        self.font = pygame.font.SysFont("georgia", 48, bold=True)
        self.hint_font = pygame.font.SysFont("consolas", 18)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in KEY_PAUSE:
            self.manager.set_state(self.playing_state)

    def draw(self, surface):
        self.playing_state.draw(surface)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        text = self.font.render("PAUSED", True, COLOR_WHITE)
        surface.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))
        hint = self.hint_font.render("Press ESC to resume", True, (200, 200, 200))
        surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)))


# ---------------------------------------------------------------- GAME OVER
class GameOverState(GameState):
    def __init__(self, manager, level_reached=1, cores_collected=0):
        super().__init__(manager)
        self.level_reached = level_reached
        self.cores_collected = cores_collected
        self.font = pygame.font.SysFont("georgia", 44, bold=True)
        self.stat_font = pygame.font.SysFont("consolas", 20)
        self.hint_font = pygame.font.SysFont("consolas", 18)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.manager.set_state(MenuState(self.manager))

    def draw(self, surface):
        draw_vertical_gradient(surface, (20, 0, 0), (60, 10, 10))
        text = self.font.render("THE EXILE HAS FALLEN", True, COLOR_RED)
        surface.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))

        stats = self.stat_font.render(
            f"Reached Level {self.level_reached}  -  {self.cores_collected} Pixel Cores collected",
            True, COLOR_GOLD,
        )
        surface.blit(stats, stats.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

        hint = self.hint_font.render("Press ENTER to return to the menu", True, COLOR_WHITE)
        surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)))
