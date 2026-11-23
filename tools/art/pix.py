"""Tiny pixel-art painter.

Shapes are drawn at 6x resolution with no anti-aliasing, then each output pixel
takes the colour that covers most of its block. Drawing the same shapes at a
bigger pixel size (p) gives a chunkier, lower-detail version of the same art.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

SS = 6            # samples per output pixel, per axis
TRANSPARENT = 0   # palette index 0 is always "nothing"


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Painter:
    def __init__(self, cell, p, origin, palette, outline=None):
        self.p = p
        cw, ch = cell if isinstance(cell, tuple) else (cell, cell)
        self.nw, self.nh = cw // p, ch // p
        self.n = self.nw
        self.k = SS / p                     # design px -> big-canvas px
        self.origin = origin                # where design (0, 0) sits inside the cell
        self.scale = 1.0
        self.rot = 0.0
        self.shift = (0.0, 0.0)
        self.palette = [None] + [rgb(c) if isinstance(c, str) else c for c in palette]
        self.index = {c: i for i, c in enumerate(self.palette) if c}
        self.outline = self.col(outline) if outline else None
        self.img = Image.new('P', (self.nw * SS, self.nh * SS), 0)
        self.d = ImageDraw.Draw(self.img)

    # ---- coordinates
    def xy(self, x, y):
        x *= self.scale
        y *= self.scale
        if self.rot:
            c, s = math.cos(self.rot), math.sin(self.rot)
            x, y = x * c - y * s, x * s + y * c
        x += self.shift[0]
        y += self.shift[1]
        return ((self.origin[0] + x) * self.k, (self.origin[1] + y) * self.k)

    def col(self, c):
        c = rgb(c) if isinstance(c, str) else c
        if c not in self.index:                 # colours can be added on the fly
            self.palette.append(c)
            self.index[c] = len(self.palette) - 1
        return self.index[c]

    # ---- shapes
    def poly(self, pts, c):
        self.d.polygon([self.xy(*q) for q in pts], fill=self.col(c))

    def rect(self, x, y, w, h, c):
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], c)

    def circle(self, cx, cy, r, c):
        self.ellipse(cx, cy, r, r, c)

    def ellipse(self, cx, cy, rx, ry, c, rot=0.0):
        pts = []
        for i in range(24):
            a = i / 24 * math.tau
            x, y = rx * math.cos(a), ry * math.sin(a)
            pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
        self.poly(pts, c)

    def line(self, a, b, w, c, round_ends=True):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length * w / 2, dx / length * w / 2
        self.poly([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)], c)
        if round_ends and w >= 3:
            self.circle(a[0], a[1], w / 2, c)
            self.circle(b[0], b[1], w / 2, c)

    # ---- output
    def finish(self):
        big = np.array(self.img)
        nw, nh, S = self.nw, self.nh, SS
        blocks = big.reshape(nh, S, nw, S).transpose(0, 2, 1, 3).reshape(nh, nw, S * S)
        colours = len(self.palette)
        counts = np.stack([(blocks == i).sum(axis=2) for i in range(colours)], axis=2)
        solid = counts[:, :, 1:].sum(axis=2)
        best = counts[:, :, 1:].argmax(axis=2) + 1
        out = np.where(solid * 2 >= S * S, best, 0).astype(np.uint8)
        if self.outline:
            filled = out > 0
            near = np.zeros_like(filled)
            near[1:] |= filled[:-1]
            near[:-1] |= filled[1:]
            near[:, 1:] |= filled[:, :-1]
            near[:, :-1] |= filled[:, 1:]
            out = np.where(~filled & near, self.outline, out)
        pal = np.array([c if c else (0, 0, 0) for c in self.palette], dtype=np.uint8)
        rgba = np.zeros((nh, nw, 4), dtype=np.uint8)
        rgba[..., :3] = pal[out]
        rgba[..., 3] = np.where(out > 0, 255, 0)
        return rgba


def two_bone(shoulder, hand, l1, l2, bend=1):
    """Elbow position for a two-segment limb reaching from shoulder to hand."""
    dx, dy = hand[0] - shoulder[0], hand[1] - shoulder[1]
    dist = min(math.hypot(dx, dy), l1 + l2 - 0.01)
    dist = max(dist, abs(l1 - l2) + 0.01)
    a = math.atan2(dy, dx)
    cos_a = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    off = math.acos(max(-1, min(1, cos_a))) * bend
    return (shoulder[0] + l1 * math.cos(a + off), shoulder[1] + l1 * math.sin(a + off))


def polar(origin, angle, r):
    """Point at `angle` (radians, 0 = right, counter-clockwise, y up) from origin."""
    return (origin[0] + r * math.cos(angle), origin[1] - r * math.sin(angle))


def save_sheet(rows, path):
    """rows: list of lists of RGBA arrays (all the same size) -> one PNG, one animation per row."""
    ch, cw = rows[0][0].shape[:2]
    sheet = np.zeros((len(rows) * ch, max(len(r) for r in rows) * cw, 4), dtype=np.uint8)
    for y, row in enumerate(rows):
        for x, frame in enumerate(row):
            sheet[y * ch:(y + 1) * ch, x * cw:(x + 1) * cw] = frame
    Image.fromarray(sheet, 'RGBA').save(path, optimize=True)
