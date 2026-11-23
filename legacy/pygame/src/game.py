"""
game.py
-------
Top-level Game class: creates the window, runs the main loop at a fixed
FPS, and forwards events/updates/draws to whichever GameState is active.
"""

import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TITLE
from src.states import StateManager, MenuState


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(GAME_TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.manager = StateManager()
        self.manager.set_state(MenuState(self.manager))

    def run(self):
        while self.running:
            dt_ms = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.manager.handle_event(event)

            self.manager.update(dt_ms)
            self.manager.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
