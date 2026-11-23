"""Snow-ruin scenery: ground, platforms, props, pickups, weapon icons and backgrounds.
Everything is drawn with the same painter and palette as the characters."""
import math
import random

from pix import Painter

OUTLINE = '#15131d'
C = {
    'snow': '#f4f8ff', 'snow_mid': '#cfdcf5', 'snow_shade': '#9fb4e0', 'ice': '#8fc4ee', 'ice_dark': '#5a8fc8',
    'dirt': '#6a4a3a', 'dirt_mid': '#523a30', 'dirt_dark': '#3a2a28', 'dirt_light': '#85604a', 'pebble': '#8a7a72',
    'stone': '#8a8fa0', 'stone_mid': '#686d80', 'stone_dark': '#464a5c', 'stone_light': '#aab0c2',
    'brick': '#8a6a72', 'brick_dark': '#5a424e', 'brick_light': '#a88890',
    'navy': '#4a5478', 'navy_dark': '#2c3454', 'navy_light': '#6a76a0',
    'wood': '#8a5a34', 'wood_dark': '#5a3820', 'wood_light': '#a87848',
    'fire_red': '#e0481a', 'fire': '#ff9a2a', 'fire_yellow': '#ffd04a', 'fire_white': '#fff2a0',
    'gold': '#e6b43c', 'gold_dark': '#a0701c', 'gold_light': '#fff0a0', 'iron': '#8f95a6', 'iron_dark': '#5b6073',
    'black': '#15131d', 'leather': '#6a3a22', 'paper': '#e0d2b0', 'red': '#b83a3a', 'glow': '#ffe090',
}
PAL = sorted(set(C.values()) | {OUTLINE})


def new(w, h, p, outline=True):
    return Painter((w, h), p, (0, 0), PAL, OUTLINE if outline else None)


def wrap(P, pts, color, width):
    for dx in (-width, 0, width):
        P.poly([(x + dx, y) for x, y in pts], color)


# ------------------------------------------------------------------ ground and platforms
def ground_tile(p):
    W = H = 84
    P = new(W, H, p, outline=False)
    rng = random.Random(7)
    P.rect(0, 0, W, H, C['dirt'])
    for y0, col in ((30, C['dirt_mid']), (56, C['dirt_dark'])):           # soil bands with a wavy top
        pts = [(x, y0 + 4 * math.sin(x / W * math.tau * 2 + y0)) for x in range(0, W + 1, 4)]
        P.poly(pts + [(W, H), (0, H)], col)
    for _ in range(9):                                                      # pebbles
        x, y = rng.randint(0, W), rng.randint(36, H - 6)
        for dx in (-W, 0, W):
            P.ellipse(x + dx, y, rng.randint(3, 5), rng.randint(2, 3), C['pebble'])
            P.ellipse(x + dx - 1, y - 1, 2, 1.2, C['dirt_light'])
    cap = [(x, 17 + 3 * math.sin(x / W * math.tau * 3) + (6 if (x // 7) % 3 == 0 else 0) * (1 + math.sin(x))) for x in range(0, W + 1, 3)]
    P.poly([(0, 0), (W, 0)] + cap[::-1], C['snow'])
    shade = [(x, 17 + 3 * math.sin(x / W * math.tau * 3) + (6 if (x // 7) % 3 == 0 else 0) * (1 + math.sin(x)) - 5) for x in range(0, W + 1, 3)]
    P.poly([(0, 6)] + shade + [(W, 6)], C['snow_mid'])
    P.poly([(0, 0), (W, 0), (W, 6), (0, 6)], C['snow'])
    return P.finish()


def stone_tile(p, kind):
    W = H = 42
    P = new(W, H, p, outline=False)
    base, dark, light = {'gray': (C['stone'], C['stone_dark'], C['stone_light']),
                         'brick': (C['brick'], C['brick_dark'], C['brick_light']),
                         'navy': (C['navy'], C['navy_dark'], C['navy_light'])}[kind]
    P.rect(0, 0, W, H, dark)
    rng = random.Random({'gray': 3, 'brick': 5, 'navy': 9}[kind])
    if kind == 'brick':
        for row in range(4):
            y = row * 10.5
            off = 0 if row % 2 == 0 else 10.5
            for bx in range(-1, 3):
                x = bx * 21 + off
                for dx in (-W, 0, W):
                    P.rect(x + dx + 1, y + 1, 19, 8.5, base)
                    P.rect(x + dx + 1, y + 1, 19, 2.5, light)
    else:
        blocks = [(0, 0, 21, 14), (21, 0, 21, 21), (0, 14, 14, 14), (14, 14, 7, 7), (0, 28, 21, 14), (21, 21, 21, 21), (14, 21, 7, 7), (14, 28, 7, 14)]
        if kind == 'navy':
            blocks = [(0, 0, 14, 14), (14, 0, 14, 10), (28, 0, 14, 14), (0, 14, 21, 14), (21, 10, 21, 18), (14, 28, 28, 14), (0, 28, 14, 14)]
        for x, y, w, h in blocks:
            P.rect(x + 1, y + 1, w - 2, h - 2, base)
            P.rect(x + 1, y + 1, w - 2, 3, light)
            if rng.random() < 0.6:
                P.rect(x + 3 + rng.random() * (w - 8), y + 4 + rng.random() * (h - 8), 3, 2, dark)
    return P.finish()


def snow_cap(p):
    W, H = 42, 18
    P = new(W, H, p, outline=False)
    drips = [(x, 9 + (5 if (x // 6) % 2 else 2) + 2 * math.sin(x * 1.7)) for x in range(0, W + 1, 3)]
    P.poly([(0, 0), (W, 0)] + drips[::-1], C['snow'])
    P.poly([(0, 11), (W, 11)] + [(x, y - 3) for x, y in drips[::-1]], C['snow_mid'])
    P.rect(0, 0, W, 6, C['snow'])
    return P.finish()


# ------------------------------------------------------------------ props
def snow_blob(P, x, y, w, h):
    P.ellipse(x, y, w, h, C['snow'])
    P.ellipse(x + w * 0.2, y + h * 0.5, w * 0.8, h * 0.6, C['snow_mid'])
    P.ellipse(x, y - h * 0.2, w * 0.8, h * 0.6, C['snow'])


def rock(p, w, h, seed):
    P = new(w, h, p)
    rng = random.Random(seed)
    pts = [(2, h - 3), (3, h * 0.55), (w * 0.22, h * 0.25), (w * 0.5, 4), (w * 0.8, h * 0.3), (w - 3, h * 0.6), (w - 2, h - 3)]
    P.poly(pts, C['stone_mid'])
    P.poly([(w * 0.5, 4), (w * 0.8, h * 0.3), (w - 3, h * 0.6), (w - 2, h - 3), (w * 0.55, h - 3), (w * 0.5, h * 0.4)], C['stone_dark'])
    P.poly([(3, h * 0.55), (w * 0.22, h * 0.25), (w * 0.5, 4), (w * 0.45, h * 0.4), (w * 0.2, h * 0.6)], C['stone'])
    snow_blob(P, w * 0.45, 7, w * 0.3, h * 0.2)
    P.ellipse(w * 0.2, h - 4, w * 0.12, 3, C['snow'])
    P.ellipse(w * 0.8, h - 4, w * 0.1, 2.4, C['snow'])
    return P.finish()


def tree(p):
    W, H = 90, 132
    P = new(W, H, p)
    P.poly([(38, 126), (42, 70), (40, 40), (46, 40), (50, 70), (54, 126)], C['wood_dark'])
    P.poly([(46, 126), (48, 70), (46, 40), (50, 40), (53, 70), (56, 126)], C['wood'])
    for a, b, wd in [((42, 70), (18, 46), 4), ((18, 46), (8, 24), 2.6), ((44, 52), (70, 30), 4), ((70, 30), (82, 10), 2.4), ((46, 42), (40, 14), 3.4),
                     ((30, 56), (22, 66), 2.4), ((60, 62), (76, 60), 2.8), ((26, 40), (28, 24), 2.4), ((62, 40), (58, 20), 2.4)]:
        P.line(a, b, wd, C['wood_dark'])
    for x, y, r in [(18, 46, 4), (8, 24, 3), (70, 30, 4.5), (82, 10, 3), (40, 14, 4), (76, 60, 3.4), (28, 24, 3), (58, 20, 3.4)]:
        snow_blob(P, x, y - 2, r, r * 0.55)
    P.ellipse(46, 126, 14, 4, C['snow'])
    return P.finish()


def pillar(p):
    W, H = 42, 84
    P = new(W, H, p)
    P.rect(8, 22, 26, 56, C['stone_mid'])
    P.rect(21, 22, 13, 56, C['stone_dark'])
    P.rect(8, 22, 5, 56, C['stone'])
    P.rect(4, 74, 34, 8, C['stone'])
    P.rect(4, 74, 34, 3, C['stone_light'])
    P.rect(5, 16, 32, 8, C['stone'])
    P.line((16, 30), (22, 44), 1.4, C['black'], False)
    P.line((22, 44), (17, 58), 1.4, C['black'], False)
    P.poly([(5, 16), (37, 16), (30, 8), (12, 8)], C['stone_dark'])
    snow_blob(P, 21, 10, 14, 5)
    P.ellipse(8, 80, 6, 2.4, C['snow'])
    return P.finish()


def tombstone(p):
    W, H = 36, 48
    P = new(W, H, p)
    P.poly([(5, 44), (5, 16), (10, 8), (18, 5), (26, 8), (31, 16), (31, 44)], C['stone_mid'])
    P.poly([(18, 5), (26, 8), (31, 16), (31, 44), (22, 44), (22, 10)], C['stone_dark'])
    P.rect(16.5, 14, 3, 18, C['stone_dark'])
    P.rect(11, 19, 14, 3, C['stone_dark'])
    snow_blob(P, 18, 6, 11, 4)
    P.ellipse(18, 44, 16, 3, C['snow'])
    return P.finish()


def sign(p):
    W, H = 48, 54
    P = new(W, H, p)
    P.rect(21, 20, 6, 32, C['wood_dark'])
    P.rect(24, 20, 3, 32, C['wood'])
    P.poly([(4, 8), (44, 8), (44, 28), (4, 28)], C['wood'])
    P.rect(4, 8, 40, 4, C['wood_light'])
    P.rect(4, 24, 40, 4, C['wood_dark'])
    P.poly([(14, 17), (30, 17), (30, 13), (38, 18), (30, 23), (30, 19), (14, 19)], C['paper'])
    snow_blob(P, 24, 8, 21, 4)
    P.ellipse(24, 52, 8, 2.4, C['snow'])
    return P.finish()


def fence(p):
    W, H = 66, 42
    P = new(W, H, p)
    for y in (14, 28):
        P.rect(2, y, 62, 5, C['wood'])
        P.rect(2, y, 62, 2, C['wood_light'])
    for x in (4, 29, 54):
        P.rect(x, 6, 8, 34, C['wood_dark'])
        P.rect(x + 3, 6, 5, 34, C['wood'])
        snow_blob(P, x + 4, 7, 6, 3)
    P.ellipse(33, 40, 28, 2.6, C['snow'])
    return P.finish()


def ice_plant(p):
    W, H = 42, 42
    P = new(W, H, p)
    for x, h, w in [(6, 20, 6), (13, 30, 7), (21, 38, 8), (29, 28, 7), (35, 18, 6)]:
        P.poly([(x - w / 2, 40), (x, 40 - h), (x + w / 2, 40)], C['ice'])
        P.poly([(x, 40 - h), (x + w / 2, 40), (x, 40)], C['ice_dark'])
        P.line((x - 1, 36), (x, 40 - h + 4), 1, C['snow'], False)
    P.ellipse(21, 40, 18, 2.6, C['snow'])
    return P.finish()


def lantern(p, flame=0):
    W, H = 30, 60
    P = new(W, H, p)
    P.rect(13, 22, 4, 36, C['iron_dark'])
    P.rect(6, 54, 18, 4, C['iron_dark'])
    P.poly([(7, 8), (23, 8), (21, 3), (9, 3)], C['iron_dark'])
    P.rect(8, 8, 14, 16, C['gold_dark'])
    P.rect(10, 10, 10, 12, C['fire_yellow'] if flame % 2 == 0 else C['fire'])
    P.rect(13, 12, 4, 7, C['fire_white'])
    P.rect(6, 22, 18, 3, C['iron_dark'])
    snow_blob(P, 15, 3, 7, 2.5)
    return P.finish()


# ------------------------------------------------------------------ fire (animated)
def campfire(p, frame, big=False):
    W, H = (60, 66) if big else (48, 54)
    P = new(W, H, p)
    cx = W / 2
    base = H - 6
    P.line((cx - 15, base), (cx + 12, base - 6), 6, C['wood_dark'])
    P.line((cx + 15, base), (cx - 12, base - 6), 6, C['wood'])
    P.ellipse(cx - 17, base + 1, 5, 3.4, C['stone_mid'])
    P.ellipse(cx + 17, base + 1, 5, 3.4, C['stone_mid'])
    f = frame % 4
    sway = [0, 2, 0, -2][f]
    hgt = (34 if big else 28) + [0, 3, -2, 2][f]
    P.poly([(cx - 13, base - 4), (cx - 8 + sway, base - hgt * 0.7), (cx - 2, base - hgt * 0.5), (cx + sway * 1.5, base - hgt), (cx + 5, base - hgt * 0.55),
            (cx + 10 + sway, base - hgt * 0.65), (cx + 13, base - 4)], C['fire_red'])
    P.poly([(cx - 9, base - 4), (cx - 4 + sway, base - hgt * 0.55), (cx + sway, base - hgt * 0.8), (cx + 5, base - hgt * 0.5), (cx + 9, base - 4)], C['fire'])
    P.poly([(cx - 5, base - 4), (cx + sway * 0.6, base - hgt * 0.55), (cx + 5, base - 4)], C['fire_yellow'])
    P.poly([(cx - 2, base - 4), (cx + sway * 0.3, base - hgt * 0.3), (cx + 2, base - 4)], C['fire_white'])
    return P.finish()


# ------------------------------------------------------------------ pickups
def coin(p):
    P = new(24, 24, p)
    P.circle(12, 12, 9.5, C['gold_dark'])
    P.circle(12, 12, 7.5, C['gold'])
    P.rect(10.5, 7, 3, 10, C['gold_dark'])
    P.poly([(6, 8), (10, 5), (12, 6), (8, 10)], C['gold_light'])
    return P.finish()


def core(p):
    P = new(24, 24, p)
    P.poly([(12, 1), (22, 12), (12, 23), (2, 12)], C['gold'])
    P.poly([(12, 1), (22, 12), (12, 23)], C['gold_dark'])
    P.poly([(12, 4), (7, 11), (12, 12)], C['gold_light'])
    return P.finish()


def book(p):
    P = new(30, 30, p)
    P.rect(4, 4, 22, 24, C['leather'])
    P.rect(4, 4, 4, 24, C['wood_dark'])
    P.rect(22, 6, 3, 20, C['paper'])
    P.poly([(15, 9), (20, 15), (15, 21), (10, 15)], C['gold'])
    P.rect(4, 4, 22, 2, C['wood_light'])
    return P.finish()


def chest(p, state):
    P = new(42, 36, p)
    P.rect(3, 14, 36, 20, C['wood'])
    P.rect(3, 14, 36, 4, C['wood_light'])
    P.rect(3, 28, 36, 6, C['wood_dark'])
    for x in (8, 31):
        P.rect(x, 14, 4, 20, C['iron_dark'])
    if state == 'open':
        P.poly([(3, 14), (39, 14), (36, 3), (6, 3)], C['wood_dark'])
        P.rect(8, 8, 26, 6, C['gold'])
        P.rect(12, 6, 8, 3, C['gold_light'])
    else:
        P.poly([(3, 14), (6, 6), (14, 2), (28, 2), (36, 6), (39, 14)], C['wood_light'])
        P.poly([(3, 14), (6, 6), (14, 2), (28, 2), (36, 6), (39, 14)], C['wood'])
        P.rect(8, 4, 4, 11, C['iron_dark'])
        P.rect(30, 4, 4, 11, C['iron_dark'])
        P.rect(18, 14, 6, 8, C['gold'])
        if state == 'locked':
            P.rect(17, 17, 8, 8, C['gold_dark'])
            P.line((19, 17), (19, 13), 2, C['iron'], False)
            P.line((23, 17), (23, 13), 2, C['iron'], False)
            P.rect(20, 19, 2, 4, C['black'])
    return P.finish()


# ------------------------------------------------------------------ weapon icons (blade pointing up-right)
def weapon(p, kind):
    P = new(48, 48, p)
    P.origin = (0, 0)

    def along(t, off=0):                   # point along the diagonal from bottom-left (t=0) to top-right (t=1), `off` sideways
        x, y = 8 + 32 * t, 40 - 32 * t
        return (x + off * 0.7071, y + off * 0.7071)

    def blade(t0, t1, w0, w1, main='iron', shade='iron_dark'):
        P.poly([along(t0, -w0), along(t1, -w1), along(t1 + 0.07, 0), along(t1, w1), along(t0, w0)], C[shade])
        P.poly([along(t0, 0), along(t1, 0), along(t1 + 0.07, 0), along(t1, w1), along(t0, w0)], '#e2e7f0')

    def shaft(t0, t1, w=2.2):
        P.line(along(t0), along(t1), w, C['wood_dark'])
    if kind == 'sword':
        shaft(0, 0.22, 3.4)
        P.line(along(0.22, -6), along(0.22, 6), 3, C['gold_dark'])
        blade(0.22, 0.95, 2.8, 1.2)
    elif kind == 'spear':
        shaft(0, 0.7)
        blade(0.62, 1.0, 3.2, 0.6)
    elif kind == 'dagger':
        shaft(0.05, 0.3, 3.2)
        P.line(along(0.3, -5), along(0.3, 5), 2.6, C['gold_dark'])
        blade(0.3, 0.78, 2.6, 1)
    elif kind == 'halberd':
        shaft(0, 0.85)
        blade(0.6, 0.84, 6, 2)
        blade(0.84, 1.0, 1.6, 0.4)
    elif kind == 'falx':
        shaft(0, 0.3, 3)
        pts_out = [along(0.3, 0), along(0.55, 7), along(0.8, 9), along(0.98, 4)]
        P.poly([along(0.3, 0)] + pts_out[1:] + [along(0.98, -1), along(0.7, 3), along(0.4, 0)], '#e2e7f0')
        P.line(along(0.3, 0), along(0.55, 7), 2, C['iron_dark'], False)
    elif kind == 'axe':
        shaft(0, 0.9, 2.8)
        P.poly([along(0.62, 0), along(0.62, 11), along(0.9, 12), along(0.86, 0)], C['iron_dark'])
        P.poly([along(0.66, 1), along(0.66, 9), along(0.88, 10), along(0.85, 1)], '#e2e7f0')
    elif kind == 'double_axe':
        shaft(0, 0.9, 2.8)
        for s in (-1, 1):
            P.poly([along(0.6, 0), along(0.6, s * 11), along(0.9, s * 12), along(0.86, 0)], C['iron_dark'])
            P.poly([along(0.64, s), along(0.64, s * 9), along(0.88, s * 10), along(0.85, s)], '#e2e7f0')
    return P.finish()


# ------------------------------------------------------------------ backgrounds (seamless strips)
def clouds(p):
    W, H = 900, 150
    P = new(W, H, p, outline=False)
    rng = random.Random(11)
    for cx0 in (90, 330, 560, 790):
        base = rng.randint(80, 120)
        for k in range(rng.randint(4, 6)):
            cx = cx0 + k * 26 - 60 + rng.randint(-6, 6)
            r = rng.randint(18, 30)
            for dx in (-W, 0, W):
                P.ellipse(cx + dx, base - r * 0.6, r * 1.3, r * 0.85, '#d9d2ec')
        for k in range(rng.randint(4, 6)):
            cx = cx0 + k * 26 - 60
            r = rng.randint(14, 24)
            for dx in (-W, 0, W):
                P.ellipse(cx + dx, base - r * 0.8 - 4, r * 1.25, r * 0.8, '#f4f1fa')
        for dx in (-W, 0, W):
            P.rect(cx0 - 70 + dx, base - 2, 150, 14, '#b9b0d8')
            P.rect(cx0 - 70 + dx, base - 6, 150, 5, '#d9d2ec')
    return P.finish()


def mist(p):
    W, H = 900, 150
    P = new(W, H, p, outline=False)
    for k, (col, base, amp) in enumerate((('#6a6f98', 60, 14), ('#5a5f88', 85, 12), ('#4c5078', 110, 10))):
        pts = [(x, base + amp * math.sin(x / W * math.tau * (2 + k)) + 6 * math.sin(x / W * math.tau * (5 + k) + k)) for x in range(0, W + 1, 6)]
        P.poly(pts + [(W, H), (0, H)], col)
    return P.finish()


def forest(p):
    W, H = 900, 240
    P = new(W, H, p, outline=False)
    rng = random.Random(21)

    def pine(x, base, h, w, dark, mid, snow):
        for dx in (-W, 0, W):
            P.rect(x - 2 + dx, base - 8, 4, 8, '#2a2030')
            tiers = 4
            for t in range(tiers):
                top = base - h + t * h * 0.2
                bot = base - h * 0.15 - (tiers - 1 - t) * h * 0.04
                ww = w * (0.45 + 0.55 * (t + 1) / tiers)
                y1 = top + h * 0.34
                P.poly([(x + dx, top), (x + ww / 2 + dx, y1), (x - ww / 2 + dx, y1)], dark)
                P.poly([(x + dx, top), (x + ww / 2 + dx, y1), (x + dx, y1)], mid)
                P.poly([(x + dx, top), (x + ww * 0.22 + dx, top + h * 0.1), (x - ww * 0.22 + dx, top + h * 0.1)], snow)
    for x in range(10, W, 34):                                  # far row
        pine(x + rng.randint(-8, 8), 190, rng.randint(80, 110), 30, '#46627c', '#587890', '#dfe8f6')
    for x in range(30, W, 46):                                  # near row
        pine(x + rng.randint(-10, 10), 235, rng.randint(120, 170), 44, '#243a52', '#34506c', '#cdd9ee')
    return P.finish()


def ruins(p):
    W, H = 900, 300
    P = new(W, H, p, outline=False)
    rng = random.Random(33)
    far, near, snow = '#5c6290', '#4a4f78', '#aab4d8'
    P.rect(0, 250, W, 50, far)
    for x0, w, h in [(30, 110, 150), (200, 80, 190), (330, 130, 140), (520, 90, 210), (650, 140, 160), (820, 70, 130)]:
        for dx in (-W, 0, W):
            P.rect(x0 + dx, 262 - h, w, h, far)
            for bx in range(0, w, 14):                              # battlements, some broken
                if rng.random() < 0.7:
                    P.rect(x0 + bx + dx, 262 - h - 9, 9, 9, far)
            P.rect(x0 + dx, 262 - h - 2, w, 3, snow)
            if w > 90:                                              # arched window
                P.rect(x0 + w / 2 - 8 + dx, 262 - h + 30, 16, 34, near)
                P.ellipse(x0 + w / 2 + dx, 262 - h + 30, 8, 8, near)
            P.rect(x0 + 10 + dx, 262 - h + 90, 10, 16, near)
    for x0, w in [(120, 120), (420, 90), (740, 100)]:               # fallen walls / arches in front
        for dx in (-W, 0, W):
            P.rect(x0 + dx, 232, w, 40, near)
            P.ellipse(x0 + w / 2 + dx, 262, 22, 26, far)
            P.rect(x0 + dx, 230, w, 3, snow)
    return P.finish()
