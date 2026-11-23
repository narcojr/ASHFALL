"""The hero: a chibi knight with a long sword and a cape, drawn from a small skeleton.

Every animation frame is a pose (angles and offsets). The same pose is drawn at
three pixel sizes, so the three art tiers are literally the same character.
"""
import math

from pix import Painter, polar, two_bone, rgb

CELL = 126            # design size of one cell (divisible by 2 and 3)
ORIGIN = (63, 118)    # feet centre inside the cell

OUTLINE = '#15131d'
BASE = {
    'skin': '#f2c9a5', 'skin_shade': '#d39a78',
    'hair': '#8a5632', 'hair_light': '#b87a44', 'hair_dark': '#5a3320',
    'steel': '#c7ccd8', 'steel_mid': '#8f95a6', 'steel_dark': '#5b6073',
    'belt': '#7a4a2a', 'belt_dark': '#4e2e1a', 'boot': '#3b3b4b', 'eye': '#241a2a',
    'blade': '#e8edf6', 'blade_shade': '#9aa5ba', 'grip': '#5a3a26', 'smear': '#eaf4ff', 'smear_edge': '#9fc4f0',
}
# one look per evolution stage: cape, metal trim and blade tint
STAGES = [
    dict(cape='#2f5fd8', cape_dark='#1f3fa6', cape_light='#5b8cf5', trim='#8f95a6', buckle='#c9a23a', blade='#e8edf6', blade_shade='#9aa5ba'),
    dict(cape='#1fa3a8', cape_dark='#146a78', cape_light='#55d0c8', trim='#6f93b8', buckle='#c9a23a', blade='#e8f6f4', blade_shade='#8fb8b8'),
    dict(cape='#d99a1e', cape_dark='#9c6410', cape_light='#f5cc58', trim='#d8b04a', buckle='#fff0a0', blade='#fff4cf', blade_shade='#d4b86a'),
    dict(cape='#c4323c', cape_dark='#80202e', cape_light='#ee6a62', trim='#e0b84e', buckle='#fff0a0', blade='#ffe9d8', blade_shade='#e09a82'),
]


def palette_for(stage):
    colors = dict(BASE, **STAGES[stage])
    return colors, sorted(set(colors.values()) | {OUTLINE})


def pose(**kw):
    p = dict(breath=0, lean=0.0, legs=(0.12, 0.05, -0.12, -0.1), hand=(-40, 11), sword=-35, hand_back=(-95, 11),
             tilt=0.0, cape=(0.1, 0.0, 0), rot=0.0, shift=(0, 0), smear=None, ground=True, drop_sword=False, crouch=0)
    p.update(kw)
    return p


def draw(P, c, ps, tier):
    """Draw one pose on painter P. c = colour dict, tier 1..3 (3 = most detail)."""
    lean = ps['lean']
    hip = [0.0, -20.0 + ps['crouch']]
    legs = ps['legs']

    def leg_points(thigh, shin):
        knee = (hip[0] + 9.5 * math.sin(thigh), hip[1] + 9.5 * math.cos(thigh))
        ankle = (knee[0] + 9.5 * math.sin(shin), knee[1] + 9.5 * math.cos(shin))
        return knee, ankle

    front = leg_points(legs[0], legs[1])
    back = leg_points(legs[2], legs[3])
    if ps['ground']:                               # plant the lowest foot on the floor
        low = max(front[1][1], back[1][1]) + 2.5
        hip[1] -= low
        front = leg_points(legs[0], legs[1])
        back = leg_points(legs[2], legs[3])

    chest = (hip[0] + math.sin(lean) * 14, hip[1] - math.cos(lean) * 14 - ps['breath'])
    head = (chest[0] + math.sin(ps['tilt']) * 6 + 1.5, chest[1] - 13)
    shoulder = (chest[0] + 1, chest[1] + 4)
    shoulder_back = (chest[0] - 4, chest[1] + 4)

    def limb(top, bottom, knee, w, color, dark):
        P.line(top, knee, w, color)
        P.line(knee, bottom, w, color)
        P.line(top, knee, 1.5, dark, False)

    def leg(pts, shade):
        knee, ankle = pts
        thick = 6
        P.line(hip, knee, thick, c['steel_mid'] if shade else c['steel'])
        P.line(knee, ankle, thick - 1, c['steel_mid'] if shade else c['steel'])
        P.circle(knee[0] + 1, knee[1], 3.2, c['steel_dark'])
        P.poly([(ankle[0] - 3, ankle[1] - 2), (ankle[0] + 3, ankle[1] - 2), (ankle[0] + 7, ankle[1] + 2.5),
                (ankle[0] - 3, ankle[1] + 2.5)], c['boot'])

    # --- back arm (hand hangs behind the body)
    hb = polar(shoulder_back, math.radians(ps['hand_back'][0]), ps['hand_back'][1])
    eb = two_bone(shoulder_back, hb, 8, 7, 1)
    P.line(shoulder_back, eb, 4, c['steel_dark'])
    P.line(eb, hb, 4, c['steel_mid'])
    P.circle(hb[0], hb[1], 2.4, c['skin_shade'])

    leg(back, True)

    # --- cape
    flow, wave, lift = ps['cape']
    top_f = (chest[0] + 3, chest[1] + 2)
    top_b = (chest[0] - 6, chest[1] + 1)
    end_x = chest[0] - 9 - 26 * flow
    end_y = chest[1] + 26 - 20 * flow - lift
    w = math.sin(wave) * 2.5
    cape = [top_b, top_f, (chest[0] + 1 - 5 * flow, chest[1] + 22 - 8 * flow - lift * 0.6),
            (end_x + 8 + w, end_y + 4), (end_x + 4, end_y + 1 + w), (end_x - 1, end_y - 2 - w), (end_x - 6 - w, end_y - 6 + 3)]
    P.poly(cape, c['cape'])
    P.poly([top_b, (chest[0] - 2, chest[1] + 12), (end_x + 2, end_y - 3), (end_x - 6 - w, end_y - 6 + 3)], c['cape_dark'])
    if tier >= 2:
        P.line((chest[0] - 1, chest[1] + 4), (end_x + 6, end_y - 1), 1.6, c['cape_light'], False)

    # --- torso
    torso = [(hip[0] - 6, hip[1] + 1), (hip[0] + 6, hip[1] + 1), (chest[0] + 7, chest[1] + 3), (chest[0] - 7, chest[1] + 3)]
    P.poly(torso, c['steel_mid'])
    P.poly([(hip[0] - 1, hip[1] + 1), (hip[0] + 6, hip[1] + 1), (chest[0] + 7, chest[1] + 3), (chest[0] + 1, chest[1] + 3)], c['steel'])
    belt_y = hip[1] - 1
    P.rect(hip[0] - 6.5 + lean * 3, belt_y - 1.5, 13, 3.4, c['belt'])
    if tier >= 2:
        P.rect(hip[0] - 1.5 + lean * 3, belt_y - 1.5, 3.2, 3.4, c['buckle'])
        P.line((chest[0] - 4, chest[1] + 6), (chest[0] + 4, chest[1] + 6), 1.2, c['steel_dark'], False)
    P.circle(chest[0] + 1, chest[1] + 4, 4.2, c['trim'])         # pauldron
    P.poly([(chest[0] - 4, chest[1] + 1), (chest[0] + 5, chest[1] + 1), (chest[0] + 3, chest[1] + 7), (chest[0] - 2, chest[1] + 7)], c['cape_dark'])

    leg(front, False)

    # --- head (big, chibi proportions)
    hx, hy = head
    k = 1.32
    def hp(pts):
        return [(hx + x * k, hy + y * k) for x, y in pts]
    P.ellipse(hx, hy + 1.5, 11.5 * k, 9.2 * k, c['skin'])
    P.poly(hp([(-9, 3), (-3, 9.5), (7, 9), (5, 5)]), c['skin_shade'])
    hair_back = [(-12, 1), (-14, -7), (-10, -10), (-13, -16), (-6, -13), (-5, -20), (0, -14), (5, -19), (7, -13), (12, -15), (11, -7), (10, 1)]
    P.poly(hp(hair_back), c['hair'])
    fringe = [(-11, 0), (-11, -7), (-5, -10), (5, -10), (11, -7), (11, -1), (8, -4), (6, 1), (3, -3), (0, 2), (-3, -3), (-6, 1), (-8, -3)]
    P.poly(hp(fringe), c['hair'])
    P.poly(hp([(-11, 0), (-11, -7), (-6, -9), (-4, -1), (-8, 1)]), c['hair_dark'])
    if tier >= 2:
        P.poly(hp([(0, -9), (6, -9), (8, -6), (2, -7)]), c['hair_light'])
        P.poly(hp([(-5, -14), (-2, -13), (-4, -18)]), c['hair_light'])
    P.rect(hx + 2, hy + 1.5, 3.6, 6, c['eye'])
    P.rect(hx + 8.2, hy + 1.5, 3.6, 6, c['eye'])

    # --- sword and front arm
    hand = polar(shoulder, math.radians(ps['hand'][0]), ps['hand'][1])
    elbow = two_bone(shoulder, hand, 8, 7, -1)
    sword_dir = math.radians(ps['sword'])
    if not ps['drop_sword']:
        grip_a = polar(hand, sword_dir + math.pi, 6)
        tip = polar(hand, sword_dir, 34)
        side = (-math.sin(sword_dir), -math.cos(sword_dir))
        base = polar(hand, sword_dir, 5)
        near = lambda q, s: (q[0] + side[0] * s, q[1] + side[1] * s)
        P.line(grip_a, hand, 3, c['grip'])
        P.line(near(hand, -5), near(hand, 5), 3, c['trim'])                   # cross guard
        P.poly([near(base, -2.6), near(base, 2.6), near(tip, 1.4), tip, near(tip, -1.4)], c['blade_shade'])
        P.poly([near(base, 0), near(base, 2.6), near(tip, 1.4), tip, near(tip, 0)], c['blade'])
        if tier >= 3:
            P.line(near(base, 0), near(polar(hand, sword_dir, 26), 0), 0.9, c['blade_shade'], False)
    P.line(shoulder, elbow, 4.4, c['steel'])
    P.line(elbow, hand, 4.4, c['steel_mid'])
    P.circle(hand[0], hand[1], 2.8, c['steel_dark'])

    if ps['smear']:
        a0, a1, r = ps['smear']
        pts_out, pts_in = [], []
        steps = 9
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            pts_out.append(polar(shoulder, a, r))
            pts_in.append(polar(shoulder, a, r - 6 * math.sin(math.pi * i / steps) - 1))
        P.poly(pts_out + pts_in[::-1], c['smear'])
        P.line(pts_out[0], pts_out[-1], 0.1, c['smear'], False)
        for i in range(steps):
            P.line(pts_out[i], pts_out[i + 1], 1.4, c['smear_edge'], False)


# ------------------------------------------------------------------ animations
def idle(i):
    t = i / 6 * math.tau
    return pose(breath=1.1 * (0.5 - 0.5 * math.cos(t)), cape=(0.12, t, 0), hand=(-40, 11), sword=-32)


def run(i):
    t = i / 8 * math.tau
    out = []
    legs = []
    for ph in (t, t + math.pi):
        thigh = 0.95 * math.sin(ph)
        flex = 0.15 + 0.95 * max(0, math.sin(ph + 1.9))
        legs += [thigh, thigh - flex]
    return pose(lean=0.2, legs=tuple(legs), hand=(18 + 6 * math.sin(t), 12), sword=8 + 6 * math.sin(t),
                hand_back=(-60 - 28 * math.sin(t), 11), cape=(0.8, t * 1.5, 1), tilt=0.1)


def jump(i):
    frames = [
        pose(crouch=3, lean=0.12, legs=(0.8, -0.8, 0.6, -0.9), hand=(-10, 12), sword=-5, cape=(0.3, 0, 0), ground=True),
        pose(lean=0.1, legs=(1.15, -0.5, 0.35, -1.3), hand=(55, 13), sword=48, hand_back=(100, 11), cape=(0.55, 1.2, 8), ground=False, shift=(0, -22)),
        pose(lean=0.05, legs=(0.35, 0.05, -0.3, -0.5), hand=(70, 13), sword=70, hand_back=(120, 11), cape=(0.4, 2.5, 14), ground=False, shift=(0, -16)),
    ]
    return frames[i]


def dash(i):
    t = i / 3 * math.tau
    return pose(lean=0.55, legs=(1.15, 0.25, -1.15, -1.3), hand=(168, 10), sword=188, hand_back=(150, 10),
                cape=(1.0, t, 0), tilt=0.15, shift=(0, 0))


ATTACKS = [
    [   # swing 1: overhead to forward
        pose(lean=-0.1, legs=(0.3, 0.1, -0.35, -0.3), hand=(112, 12), sword=128, cape=(0.35, 1, 3)),
        pose(lean=0.18, legs=(0.55, 0.25, -0.5, -0.4), hand=(62, 14), sword=52, smear=(115, 30, 24), cape=(0.6, 2, 4)),
        pose(lean=0.32, legs=(0.75, 0.3, -0.6, -0.5), hand=(8, 15), sword=0, smear=(60, -35, 26), cape=(0.8, 3, 4), shift=(2, 0)),
        pose(lean=0.25, legs=(0.65, 0.25, -0.5, -0.4), hand=(-22, 13), sword=-32, cape=(0.7, 4, 2), shift=(2, 0)),
    ],
    [   # swing 2: low backhand rising
        pose(lean=0.22, legs=(0.5, 0.2, -0.5, -0.5), hand=(-72, 12), sword=-105, cape=(0.7, 1, 2), crouch=2),
        pose(lean=0.25, legs=(0.65, 0.25, -0.55, -0.5), hand=(-25, 14), sword=-15, smear=(-70, 0, 25), cape=(0.8, 2, 3)),
        pose(lean=0.15, legs=(0.6, 0.2, -0.45, -0.4), hand=(38, 15), sword=55, smear=(-10, 80, 26), cape=(0.7, 3, 5), shift=(2, 0)),
        pose(lean=0.05, legs=(0.4, 0.15, -0.3, -0.3), hand=(78, 12), sword=105, cape=(0.5, 4, 5)),
    ],
    [   # swing 3: heavy overhead chop
        pose(lean=-0.28, legs=(0.35, 0.1, -0.5, -0.5), hand=(138, 11), sword=158, cape=(0.3, 1, 6), crouch=2),
        pose(lean=-0.02, legs=(0.5, 0.2, -0.45, -0.4), hand=(105, 13), sword=98, smear=(150, 85, 25), cape=(0.45, 2, 6)),
        pose(lean=0.38, legs=(0.9, 0.35, -0.7, -0.6), hand=(12, 15), sword=-8, smear=(95, -40, 28), cape=(0.9, 3, 3), shift=(3, 0), crouch=2),
        pose(lean=0.32, legs=(0.8, 0.3, -0.6, -0.5), hand=(-40, 13), sword=-58, cape=(0.8, 4, 1), shift=(3, 0), crouch=2),
    ],
]


def hurt(i):
    return [pose(lean=-0.32, tilt=-0.2, legs=(0.35, 0.2, -0.3, -0.5), hand=(40, 12), sword=60, hand_back=(120, 11), cape=(0.5, 1, 4)),
            pose(lean=-0.45, tilt=-0.3, legs=(0.5, 0.3, -0.2, -0.4), hand=(55, 11), sword=75, hand_back=(130, 11), cape=(0.6, 2, 6), shift=(-2, 0))][i]


def death(i):
    return [
        pose(lean=-0.35, tilt=-0.2, legs=(0.3, 0.2, -0.25, -0.4), hand=(45, 12), sword=70, cape=(0.5, 1, 5), shift=(-2, 0)),
        pose(lean=-0.6, tilt=-0.3, crouch=5, legs=(0.9, -0.7, 0.4, -0.9), hand=(70, 12), sword=95, hand_back=(120, 11), cape=(0.5, 2, 8), shift=(-4, 0)),
        pose(lean=-0.5, crouch=9, legs=(1.4, -1.4, 0.9, -1.5), hand=(-60, 12), sword=-80, cape=(0.3, 3, 2), shift=(-4, 0)),
        pose(rot=-0.9, ground=False, lean=-0.1, legs=(0.4, 0.1, -0.2, -0.2), hand=(80, 12), sword=100, cape=(0.4, 3, 6), shift=(-10, -8)),
        pose(rot=-1.5, ground=False, lean=0, legs=(0.2, 0.1, -0.1, -0.1), hand=(60, 12), sword=75, cape=(0.2, 3, 2), shift=(-4, -6)),
        pose(rot=-1.55, ground=False, lean=0, legs=(0.15, 0.1, -0.1, -0.1), hand=(-30, 12), sword=-30, cape=(0.1, 3, 0), shift=(-4, -6), drop_sword=True),
    ][i]


ANIMS = [   # name, frame count, builder, fps, loops
    ('idle', 6, idle, 6, True),
    ('run', 8, run, 14, True),
    ('jump', 3, jump, 8, False),
    ('dash', 3, dash, 17, False),
    ('attack', 12, lambda i: ATTACKS[i // 4][i % 4], 13, False),
    ('hurt', 2, hurt, 12, False),
    ('death', 6, death, 6, False),
]


def render(tier_p, stage):
    """All frames for one pixel size and one evolution stage -> list of rows."""
    colors, pal = palette_for(stage)
    rows = []
    for name, n, build, fps, loop in ANIMS:
        row = []
        for i in range(n):
            P = Painter(CELL, tier_p, ORIGIN, pal, OUTLINE)
            ps = build(i)
            P.rot = ps['rot']
            P.shift = ps['shift']
            draw(P, colors, ps, {3: 1, 2: 2, 1: 3}[tier_p])
            row.append(P.finish())
        rows.append(row)
    return rows
