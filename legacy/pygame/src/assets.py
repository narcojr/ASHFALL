"""
assets.py
---------
Tiny helper for loading sprite images. If you drop a real PNG into
assets/images/ with the matching filename, it will be used automatically.
If the file doesn't exist, a simple colored placeholder rectangle is drawn
instead, so the game always runs even with missing art.

Also supports `tint`: a cheap palette-swap so one piece of art (e.g. the
Royal Knight) can be reused for a tougher variant (Royal Knight II, or the
final boss) just by multiplying its colors by a tint color - no extra art
needed.
"""

import os
import pygame

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "images")

_cache = {}


def load_image(filename, size, fallback_color, tint=None):
    """
    Load assets/images/<filename>, scaled to `size`.
    Falls back to a flat-colored placeholder surface if the file is missing.
    `tint`, if given as an (r, g, b) tuple, multiplies the loaded image's
    colors (a quick palette swap) without needing separate art files.
    """
    key = (filename, size, tint)
    if key in _cache:
        return _cache[key]

    path = os.path.join(ASSETS_DIR, filename)
    surface = None
    if os.path.isfile(path):
        try:
            surface = pygame.image.load(path).convert_alpha()
            surface = pygame.transform.smoothscale(surface, size)
        except pygame.error:
            surface = None

    if surface is None:
        surface = make_placeholder(size, fallback_color)
    elif tint is not None:
        surface = tint_surface(surface, tint)

    _cache[key] = surface
    return surface


def tint_surface(surface, color):
    """Multiply-blend a color over a surface, preserving its alpha shape."""
    tinted = surface.copy()
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((color[0], color[1], color[2], 255))
    tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return tinted


def make_placeholder(size, color):
    """Draw a simple pixel-art-ish placeholder block (body + darker outline)."""
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    body_rect = pygame.Rect(0, 0, w, h)
    surf.fill(color, body_rect)
    darker = tuple(max(0, c - 60) for c in color[:3])
    pygame.draw.rect(surf, darker, body_rect, width=2)
    eye_y = int(h * 0.28)
    pygame.draw.rect(surf, (20, 20, 20), (int(w * 0.25), eye_y, 3, 3))
    pygame.draw.rect(surf, (20, 20, 20), (int(w * 0.65), eye_y, 3, 3))
    return surf


def load_texture_tile(filename, tile_size=64):
    """Load a seamless texture (stone/brick) at a fixed square tile size."""
    return load_image(filename, (tile_size, tile_size), (90, 90, 95))


def draw_tiled(surface, dest_rect, texture, scroll_x=0):
    """
    Blit `texture` repeatedly to fill dest_rect (a screen-space pygame.Rect),
    offset horizontally by scroll_x so the pattern appears to scroll with
    the camera instead of swimming in place.
    """
    tw, th = texture.get_size()
    if tw <= 0 or th <= 0:
        return
    start_x = dest_rect.x - (scroll_x % tw)
    y = dest_rect.y
    while y < dest_rect.bottom:
        x = start_x
        while x < dest_rect.right:
            surface.blit(texture, (x, y))
            x += tw
        y += th
