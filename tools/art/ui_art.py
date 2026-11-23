"""Menu and HUD art. One UI pixel = 3 screen pixels (the same chunk size as the Level 1 world)."""
import math

import numpy as np
from PIL import Image

from font import bitmap
from pix import Painter

OUTLINE = '#15131d'
U = {
    'stone': '#8a8fa0', 'stone_mid': '#686d80', 'stone_dark': '#464a5c', 'stone_light': '#b4bacc',
    'snow': '#f4f8ff', 'snow_mid': '#cfdcf5', 'ice': '#8fc4ee', 'ice_dark': '#5a8fc8', 'navy': '#232744', 'navy_dark': '#181b32',
    'navy_light': '#2f3560', 'gold': '#e6b43c', 'gold_dark': '#a0701c', 'red': '#d24a4a', 'red_dark': '#7a2230',
    'green': '#6cc24a', 'green_dark': '#3a7a2a', 'blue': '#4a8ae0', 'blue_dark': '#24468a', 'white': '#ffffff',
}


def new(w, h):
    return Painter((w, h), 1, (0, 0), [], OUTLINE)


def button(state):
    W, H = 84, 18
    P = new(W, H)
    body = {'normal': ('stone', 'stone_mid'), 'hover': ('stone_light', 'stone')}[state]
    P.rect(1, 2, W - 2, H - 3, U[body[1]])
    for row in range(3):                                      # brick rows
        y = 3 + row * 5
        for x in range(-6 + (row % 2) * 6, W, 12):
            P.rect(x + 1, y, 10, 4, U[body[0]])
    P.rect(1, 2, W - 2, 2, U['snow'])                         # frost
    for x in range(2, W - 2, 6):
        P.rect(x, 4, 3, 2 + (x * 7 % 3), U['snow_mid'])
    P.rect(1, H - 3, W - 2, 2, U['stone_dark'])
    return P.finish()


def pause_button():
    P = new(14, 14)
    P.rect(1, 2, 12, 11, U['stone_mid'])
    P.rect(1, 2, 12, 2, U['snow'])
    P.rect(4, 5, 2, 6, U['snow'])
    P.rect(8, 5, 2, 6, U['snow'])
    return P.finish()


def panel():
    W = H = 24
    P = new(W, H)
    P.rect(0, 0, W, H, U['stone_dark'])
    P.rect(1, 1, W - 2, H - 2, U['stone_mid'])
    P.rect(3, 3, W - 6, H - 6, U['navy_dark'])
    P.rect(4, 4, W - 8, H - 8, U['navy'])
    P.rect(0, 0, W, 2, U['snow'])
    P.rect(0, 2, W, 1, U['snow_mid'])
    return P.finish()


def icons():
    """sheet of small HUD icons, 8x8 each: heart, bolt, core, dash"""
    P = new(32, 8)
    P.poly([(0.5, 2), (2, 0.5), (4, 2), (6, 0.5), (7.5, 2), (7.5, 4), (4, 7.5), (0.5, 4)], U['red'])
    P.rect(1.5, 1.5, 1, 1, U['snow'])
    P.poly([(13, 0), (10, 4.4), (12.6, 4.4), (11, 8), (15.5, 3), (13, 3), (14.5, 0)], U['gold'])
    P.poly([(20, 0.5), (23.5, 4), (20, 7.5), (16.5, 4)], U['gold'])
    P.rect(19.5, 2, 1, 1, U['snow'])
    P.poly([(24.5, 3), (28, 3), (28, 1.5), (31.5, 4), (28, 6.5), (28, 5), (24.5, 5)], U['ice'])
    return P.finish()


def logo():
    """ASHFALL in chunky ice letters, one font pixel = 3 art pixels."""
    text, scale = 'ASHFALL', 3
    adv = 6 * scale
    W, H = len(text) * adv + 10, 7 * scale + 16
    P = new(W, H)
    for i, ch in enumerate(text):
        ox = 5 + i * adv
        for ry, row in enumerate(bitmap(ch)):
            for rx, bit in enumerate(row):
                if bit != '1':
                    continue
                x, y = ox + rx * scale, 4 + ry * scale
                P.rect(x + 1, y + 1, scale, scale, U['navy'])         # drop shadow
                P.rect(x, y, scale, scale, U['snow'] if ry < 3 else U['ice'] if ry < 6 else U['ice_dark'])
        for rx in (0, 2, 4):                                              # icicles hang from the bottom row
            if bitmap(ch)[6][rx] == '1' and (rx + i) % 2 == 0:
                x = ox + rx * scale
                P.poly([(x, 4 + 7 * scale), (x + scale, 4 + 7 * scale), (x + scale / 2, 4 + 7 * scale + 5 + (i % 3) * 2)], U['ice'])
    return P.finish()


def save(arr, path, scale=1):
    im = Image.fromarray(arr, 'RGBA')
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(path, optimize=True)
