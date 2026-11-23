"""
camera.py
---------
A minimal side-scrolling camera. It keeps the player roughly centered and
clamps so you never see past the edges of the level.
"""

import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    def __init__(self, level_width_px):
        self.offset_x = 0
        self.offset_y = 0
        self.level_width_px = level_width_px

    def update(self, target_rect):
        desired_x = target_rect.centerx - SCREEN_WIDTH // 2
        self.offset_x = max(0, min(desired_x, max(0, self.level_width_px - SCREEN_WIDTH)))
        # No vertical scrolling needed for this level, keep it simple.
        self.offset_y = 0

    def apply(self, rect):
        """Return a copy of rect shifted into screen space."""
        return pygame.Rect(rect.x - self.offset_x, rect.y - self.offset_y, rect.width, rect.height)

    def apply_point(self, x, y):
        return (x - self.offset_x, y - self.offset_y)
