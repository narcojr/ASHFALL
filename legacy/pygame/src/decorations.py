"""
decorations.py
---------------
Purely visual props scattered through generated levels for atmosphere -
campfires and tombstones. They have no collision and don't affect
gameplay; they just make the wasteland feel lived-in (and let each level
look a little different).
"""

import pygame
from src import assets
from src.data import ITEM_ICONS


class Decoration:
    SIZE = 40
    KIND_ICON = {
        "campfire": ITEM_ICONS["campfire"],
        "tombstone": ITEM_ICONS["tombstone"],
    }
    KIND_FALLBACK_COLOR = {
        "campfire": (200, 100, 40),
        "tombstone": (90, 90, 95),
    }

    def __init__(self, x, y, kind):
        self.kind = kind
        self.rect = pygame.Rect(x, y - self.SIZE, self.SIZE, self.SIZE)
        icon_file = self.KIND_ICON.get(kind)
        fallback = self.KIND_FALLBACK_COLOR.get(kind, (120, 120, 120))
        self.image = assets.load_image(icon_file, (self.SIZE, self.SIZE), fallback)

    def draw(self, surface, camera):
        surface.blit(self.image, camera.apply(self.rect))
