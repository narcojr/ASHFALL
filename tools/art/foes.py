"""Enemies: footman, royal knight, elite knight, witch and the boss (The Dominion).
Same skeleton idea as the hero, so everything in the game moves the same way."""
import math

from pix import Painter, polar, two_bone, rgb

CELL = 126
ORIGIN = (63, 118)
BOSS_CELL = 180
BOSS_ORIGIN = (90, 166)
OUTLINE = '#15131d'

COMMON = {'skin': '#e0b896', 'bone': '#d8d0b8', 'wood': '#8a5a34', 'wood_dark': '#5a3820', 'iron': '#8f95a6', 'iron_dark': '#5b6073',
          'blade': '#e2e7f0', 'blade_shade': '#8f9ab0', 'grip': '#4a3220', 'smear': '#f2e4d8', 'smear_edge': '#c9a090'}

STYLES = {
    'footman': dict(
        body='#6d7280', body_dark='#464a58', body_light='#8f95a6', cloth='#7a4a2a', cloth_dark='#4e2e1a', trim='#8f95a6',
        helm='bucket', shield='round', weapon=26, plume=None, cape=None, glow='#d8c060', scale=1.0),
    'royal': dict(
        body='#b3b9cb', body_dark='#7a8095', body_light='#dde2ee', cloth='#9c2f2f', cloth_dark='#641c22', trim='#d6a93a',
        helm='crest', shield='kite', weapon=34, plume='#c0392b', cape=None, glow='#ffd070', scale=1.0, emblem='#e0782a'),
    'elite': dict(
        body='#4a5066', body_dark='#2c3042', body_light='#6c7490', cloth='#1c6a68', cloth_dark='#124648', trim='#38c0a8',
        helm='horned', shield='kite', weapon=36, plume=None, cape=('#1c6a68', '#124648'), glow='#60f0d0', scale=1.0, emblem='#38c0a8'),
    'boss': dict(
        body='#2c2230', body_dark='#18121c', body_light='#4a3a52', cloth='#7a1c24', cloth_dark='#4a0e16', trim='#c8a040',
        helm='crown', shield=None, weapon=46, plume=None, cape=('#7a1c24', '#4a0e16'), glow='#ff4030', scale=1.45),
}
WITCH = {'robe': '#3a5ccf', 'robe_dark': '#233a8c', 'robe_light': '#6c8cf0', 'hood_dark': '#17204f', 'face': '#0e1226',
         'eye': '#7af0ff', 'staff': '#6a4a30', 'orb': '#8a5af0', 'orb_light': '#d4b8ff', 'trim': '#c8a040'}


def palette_for(name):
    if name == 'witch':
        cols = dict(WITCH)
    else:
        cols = dict(COMMON, **STYLES[name])
        cols = {k: v for k, v in cols.items() if isinstance(v, str) and v.startswith('#')}
        if STYLES[name]['cape']:
            cols['cape'], cols['cape_dark'] = STYLES[name]['cape']
    return cols, sorted(set(cols.values()) | {OUTLINE})


def pose(**kw):
    p = dict(breath=0, lean=0.0, legs=(0.1, 0.05, -0.1, -0.1), hand=(-30, 11), sword=-30, hand_back=(-70, 9), tilt=0.0,
             cape=(0.1, 0.0, 0), rot=0.0, shift=(0, 0), smear=None, ground=True, crouch=0, shield_up=0, drop=False,
             staff=80, orb=1.0, hover=0, sway=0.0)
    p.update(kw)
    return p


# ------------------------------------------------------------------ humanoid foes
def draw_humanoid(P, c, ps, s, tier):
    lean = ps['lean']
    hip = [0.0, -19.0 + ps['crouch']]
    legs = ps['legs']

    def leg_points(thigh, shin):
        knee = (hip[0] + 9 * math.sin(thigh), hip[1] + 9 * math.cos(thigh))
        return knee, (knee[0] + 9 * math.sin(shin), knee[1] + 9 * math.cos(shin))

    front, back = leg_points(legs[0], legs[1]), leg_points(legs[2], legs[3])
    if ps['ground']:
        hip[1] -= max(front[1][1], back[1][1]) + 2.5
        front, back = leg_points(legs[0], legs[1]), leg_points(legs[2], legs[3])

    chest = (hip[0] + math.sin(lean) * 14, hip[1] - math.cos(lean) * 14 - ps['breath'])
    head = (chest[0] + math.sin(ps['tilt']) * 5 + 1, chest[1] - 13)
    shoulder = (chest[0] + 1, chest[1] + 4)
    shoulder_back = (chest[0] - 4, chest[1] + 4)

    def leg(pts, dark):
        knee, ankle = pts
        col = c['body_dark'] if dark else c['body']
        P.line(hip, knee, 6, col)
        P.line(knee, ankle, 5.2, col)
        P.poly([(ankle[0] - 3, ankle[1] - 2), (ankle[0] + 3, ankle[1] - 2), (ankle[0] + 7, ankle[1] + 2.5), (ankle[0] - 3, ankle[1] + 2.5)], c['cloth_dark'])

    # back arm (+ shield in front of the body later)
    hb = polar(shoulder_back, math.radians(ps['hand_back'][0]), ps['hand_back'][1])
    eb = two_bone(shoulder_back, hb, 8, 7, 1)
    P.line(shoulder_back, eb, 4, c['body_dark'])
    P.line(eb, hb, 4, c['body_dark'])
    leg(back, True)

    if s['cape']:
        flow, wave, lift = ps['cape']
        end_x = chest[0] - 8 - 20 * flow
        end_y = chest[1] + 24 - 16 * flow - lift
        w = math.sin(wave) * 2.2
        P.poly([(chest[0] - 6, chest[1] + 1), (chest[0] + 2, chest[1] + 2), (end_x + 8 + w, end_y + 4), (end_x + 2, end_y + 1 + w), (end_x - 5 - w, end_y - 4)], c['cape'])
        P.poly([(chest[0] - 6, chest[1] + 1), (chest[0] - 2, chest[1] + 12), (end_x - 5 - w, end_y - 4)], c['cape_dark'])

    # torso
    P.poly([(hip[0] - 6.5, hip[1] + 1), (hip[0] + 6.5, hip[1] + 1), (chest[0] + 7.5, chest[1] + 3), (chest[0] - 7.5, chest[1] + 3)], c['body'])
    P.poly([(hip[0] - 1, hip[1] + 1), (hip[0] + 6.5, hip[1] + 1), (chest[0] + 7.5, chest[1] + 3), (chest[0] + 1, chest[1] + 3)], c['body_light'])
    P.poly([(hip[0] - 6.5, hip[1] + 4), (hip[0] + 6.5, hip[1] + 4), (hip[0] + 7, hip[1] + 9), (hip[0] - 7, hip[1] + 9)], c['cloth'])   # tabard/skirt
    P.rect(hip[0] - 7 + lean * 3, hip[1] - 1.5, 14, 3.4, c['cloth_dark'])
    P.circle(chest[0] + 1, chest[1] + 4, 4.6, c['trim'] if tier >= 2 else c['body_dark'])
    if tier >= 2 and s['helm'] != 'bucket':
        P.line((chest[0] - 4, chest[1] + 7), (chest[0] + 4, chest[1] + 7), 1.2, c['body_dark'], False)

    leg(front, False)

    # head (helmet)
    hx, hy = head
    k = 1.3
    def hp(pts):
        return [(hx + x * k, hy + y * k) for x, y in pts]
    kind = s['helm']
    P.ellipse(hx, hy + 0.5, 11 * k, 9.5 * k, c['body'])
    P.poly(hp([(-10, 2), (-6, 9), (6, 9), (10, 2), (10, 8), (-10, 8)]), c['body_dark'])
    P.poly(hp([(0, -8), (7, -8), (9, -3), (2, -5)]), c['body_light'])
    P.rect(hx - 8 * k + 6, hy + 0.5 * k, 16 * k - 6, 3 * k, c['body_dark'])            # visor slit area
    eye = c['glow']
    P.rect(hx + 2, hy + 1.5 * k, 4 * k * 0.6, 1.8 * k * 0.9, eye)
    P.rect(hx + 8, hy + 1.5 * k, 4 * k * 0.6, 1.8 * k * 0.9, eye)
    if kind == 'crest':
        P.poly(hp([(-3, -9), (6, -9), (3, -17), (-6, -22), (-12, -17), (-5, -14)]), s['plume'] and c['cloth'] or c['body'])
    elif kind == 'horned':
        P.poly(hp([(-9, -4), (-15, -12), (-14, -20), (-8, -11), (-4, -7)]), c['bone'])
        P.poly(hp([(9, -4), (15, -10), (16, -19), (9, -9), (4, -7)]), c['bone'])
    elif kind == 'crown':
        P.poly(hp([(-11, -5), (-11, -16), (-6, -9), (-3, -19), (1, -9), (5, -18), (8, -8), (12, -15), (11, -5)]), c['trim'])
        P.poly(hp([(-11, -5), (11, -5), (10, -2), (-10, -2)]), c['cloth_dark'])
    elif kind == 'bucket' and tier >= 2:
        P.line((hx - 6 * k, hy - 5 * k), (hx + 6 * k, hy - 5 * k), 1.2, c['iron_dark'], False)

    # shield on the off hand
    shield = s['shield']
    if shield:
        sc = (chest[0] + 3, chest[1] + 10 + ps['shield_up'])
        if shield == 'round':
            P.circle(sc[0], sc[1], 9, c['iron_dark'])
            P.circle(sc[0], sc[1], 7.2, c['wood'])
            P.circle(sc[0], sc[1], 2.4, c['iron'])
            if tier >= 2:
                P.line((sc[0] - 6, sc[1]), (sc[0] + 6, sc[1]), 1, c['wood_dark'], False)
        else:
            P.poly([(sc[0] - 8, sc[1] - 10), (sc[0] + 8, sc[1] - 10), (sc[0] + 8, sc[1] + 2), (sc[0], sc[1] + 12), (sc[0] - 8, sc[1] + 2)], c['trim'])
            P.poly([(sc[0] - 6, sc[1] - 8), (sc[0] + 6, sc[1] - 8), (sc[0] + 6, sc[1] + 1), (sc[0], sc[1] + 9), (sc[0] - 6, sc[1] + 1)], c['emblem'])
            if tier >= 2:
                P.line((sc[0], sc[1] - 7), (sc[0], sc[1] + 7), 1.4, c['body_dark'], False)

    # weapon arm
    hand = polar(shoulder, math.radians(ps['hand'][0]), ps['hand'][1])
    elbow = two_bone(shoulder, hand, 8, 7, -1)
    if not ps['drop']:
        d = math.radians(ps['sword'])
        length = s['weapon']
        tip = polar(hand, d, length)
        base = polar(hand, d, 5)
        side = (-math.sin(d), -math.cos(d))
        near = lambda q, o: (q[0] + side[0] * o, q[1] + side[1] * o)
        width = 2.6 if length < 40 else 3.6
        P.line(polar(hand, d + math.pi, 6), hand, 3, c['grip'])
        P.line(near(hand, -5), near(hand, 5), 3, c['iron_dark'])
        P.poly([near(base, -width), near(base, width), near(tip, 1.2), tip, near(tip, -1.2)], c['blade_shade'])
        P.poly([near(base, 0), near(base, width), near(tip, 1.2), tip, near(tip, 0)], c['blade'])
    P.line(shoulder, elbow, 4.4, c['body'])
    P.line(elbow, hand, 4.4, c['body_dark'])
    P.circle(hand[0], hand[1], 2.8, c['iron_dark'])

    if ps['smear']:
        a0, a1, r = ps['smear']
        out, inn = [], []
        for i in range(10):
            a = math.radians(a0 + (a1 - a0) * i / 9)
            out.append(polar(shoulder, a, r))
            inn.append(polar(shoulder, a, r - 6 * math.sin(math.pi * i / 9) - 1))
        P.poly(out + inn[::-1], c['smear'])
        for i in range(9):
            P.line(out[i], out[i + 1], 1.4, c['smear_edge'], False)


# ------------------------------------------------------------------ the witch
def draw_witch(P, c, ps, tier):
    sway = ps['sway']
    base_y = -ps['hover']
    top = (math.sin(ps['lean']) * 8 + sway, base_y - 40)
    hem = [(-13 + sway * 0.3, base_y), (-8, base_y + 3 + sway * 0.2), (-2, base_y), (4, base_y + 3), (10, base_y), (14 + sway * 0.3, base_y + 1)]
    P.poly([(top[0] - 8, top[1] + 4), (top[0] + 8, top[1] + 4)] + hem[::-1], c['robe'])
    P.poly([(top[0] - 8, top[1] + 4), (top[0] - 1, top[1] + 4), (hem[3][0] - 2, hem[3][1]), (hem[0][0], hem[0][1])], c['robe_dark'])
    if tier >= 2:
        P.line((top[0] + 3, top[1] + 8), (top[0] + 6, base_y - 2), 1.4, c['robe_light'], False)
    P.rect(top[0] - 6, top[1] + 17, 12, 2.6, c['trim'])
    # staff and the orb that is her attack
    hand = polar((top[0] + 2, top[1] + 12), math.radians(ps['hand'][0]), ps['hand'][1])
    sa = math.radians(ps['staff'])
    foot = polar(hand, sa + math.pi, 22)
    head_pt = polar(hand, sa, 26)
    P.line(foot, head_pt, 2.6, c['staff'])
    P.circle(head_pt[0], head_pt[1], 3.2 * ps['orb'], c['trim'])
    P.circle(head_pt[0], head_pt[1], 6 * ps['orb'], c['orb'])
    P.circle(head_pt[0] - 1, head_pt[1] - 1, 2.4 * ps['orb'], c['orb_light'])
    elbow = two_bone((top[0] + 2, top[1] + 8), hand, 7, 7, -1)
    P.line((top[0] + 2, top[1] + 8), elbow, 5, c['robe_dark'])
    P.line(elbow, hand, 5, c['robe'])
    P.circle(hand[0], hand[1], 2.6, c['face'])
    # hood and face
    hx, hy = top[0] + 1, top[1] - 7
    P.ellipse(hx, hy + 2, 13, 12, c['robe'])
    P.poly([(hx - 13, hy + 6), (hx - 9, hy - 8), (hx, hy - 20), (hx + 6, hy - 10), (hx + 13, hy + 4)], c['robe'])
    P.poly([(hx - 13, hy + 6), (hx - 9, hy - 8), (hx - 2, hy - 14), (hx - 4, hy + 4)], c['robe_dark'])
    P.ellipse(hx + 3, hy + 2, 8.5, 9, c['hood_dark'])
    P.ellipse(hx + 4, hy + 3, 6.5, 7.2, c['face'])
    P.rect(hx + 2, hy + 1, 3, 2.6, c['eye'])
    P.rect(hx + 7.5, hy + 1, 3, 2.6, c['eye'])


# ------------------------------------------------------------------ animations
# Every foe shares the hero's skeleton and pixel style, but each one moves in its
# own way: idle, walk and attack poses are authored per character.
def _t(i, n):
    return i / n * math.tau


def walk(i):
    t = _t(i, 6)
    legs = []
    for ph in (t, t + math.pi):
        th = 0.6 * math.sin(ph)
        legs += [th, th - (0.1 + 0.55 * max(0, math.sin(ph + 1.9)))]
    return pose(lean=0.07, legs=tuple(legs), hand=(30, 10), sword=70 + 6 * math.sin(t), hand_back=(-60, 9), shield_up=math.sin(t * 2), cape=(0.3, t, 0))


def idle(i):
    t = i / 4 * math.tau
    return pose(breath=0.9 * (0.5 - 0.5 * math.cos(t)), hand=(25, 10), sword=78, cape=(0.12, t, 0), sway=math.sin(t) * 1.5, hover=1.5 + math.sin(t) * 1.2)


# ---- footman: a nervous conscript. Quick shallow breath, shield fidgeting, sword tip wagging.
def idle_footman(i):
    t = _t(i, 4)
    return pose(breath=0.8 * (0.5 - 0.5 * math.cos(t)), hand=(25 + 6 * math.sin(t), 10), sword=76 + 12 * math.sin(t),
                tilt=0.14 * math.sin(t), shield_up=1 + 1.6 * math.sin(t + 1), cape=None,
                legs=(0.16, 0.08, -0.14, -0.12))


def walk_footman(i):
    t = _t(i, 6)
    legs = []
    for ph in (t, t + math.pi):
        th = 0.5 * math.sin(ph)
        legs += [th, th - (0.12 + 0.5 * max(0, math.sin(ph + 1.9)))]
    return pose(lean=0.15, legs=tuple(legs), hand=(30, 10), sword=64 + 5 * math.sin(t),
                hand_back=(-60, 9), shield_up=1.2 + math.sin(t * 2), cape=None)


ATTACK_FOOTMAN = [
    pose(lean=-0.1, hand=(95, 12), sword=118, legs=(0.25, 0.1, -0.3, -0.3), shield_up=0),
    pose(lean=-0.22, hand=(118, 12), sword=138, legs=(0.3, 0.1, -0.38, -0.4), crouch=1.2, shield_up=-1),
    pose(lean=0.32, hand=(18, 15), sword=10, legs=(0.7, 0.3, -0.55, -0.45), smear=(95, -40, 24), shift=(3, 0)),
    pose(lean=0.28, hand=(-26, 13), sword=-30, legs=(0.6, 0.3, -0.5, -0.42), shift=(3, 0)),
    pose(lean=0.08, hand=(14, 11), sword=44, legs=(0.3, 0.1, -0.25, -0.25), shift=(1, 0)),
]

# ---- royal knight: a proud sentinel. Slow salute, chin up, braced kite shield, marching steps.
def idle_royal(i):
    t = _t(i, 4)
    lift = 0.5 - 0.5 * math.cos(t)                     # blade rises to a salute and returns
    return pose(breath=0.7 * (0.5 - 0.5 * math.cos(t)), lean=-0.05, tilt=-0.06,
                hand=(25 - 48 * lift, 10), sword=78 - 42 * lift, hand_back=(-70, 9), shield_up=-1,
                cape=None, legs=(0.12, 0.06, -0.16, -0.12))


def walk_royal(i):
    t = _t(i, 6)
    legs = []
    for ph in (t, t + math.pi):
        th = 0.55 * math.sin(ph)
        legs += [th, th - (0.16 + 0.7 * max(0, math.sin(ph + 1.7)))]     # snappy high-knee march
    return pose(lean=0.02, legs=tuple(legs), hand=(62, 10), sword=88, hand_back=(-66, 9),
                shield_up=math.sin(t * 2) * 1.2, cape=None)


ATTACK_ROYAL = [
    pose(lean=-0.14, hand=(105, 12), sword=130, legs=(0.3, 0.12, -0.35, -0.35), shield_up=-2),
    pose(lean=-0.3, hand=(128, 13), sword=150, legs=(0.35, 0.12, -0.45, -0.45), shield_up=-3),
    pose(lean=0.34, hand=(40, 15), sword=-4, legs=(0.75, 0.3, -0.6, -0.5), smear=(60, -20, 26), shift=(5, 0)),
    pose(lean=0.3, hand=(30, 14), sword=-8, legs=(0.65, 0.28, -0.55, -0.45), shift=(4, 0)),
    pose(lean=0.1, hand=(45, 11), sword=55, legs=(0.3, 0.1, -0.28, -0.25), shift=(2, 0)),
]

# ---- elite knight: a stalking hunter. Coiled crouch, weight shifting side to side, rippling cape.
def idle_elite(i):
    t = _t(i, 4)
    return pose(crouch=2.2, breath=0.6 * (0.5 - 0.5 * math.cos(t)), lean=0.14,
                shift=(2.2 * math.sin(t), 0), tilt=0.1 * math.sin(t + 0.6),
                hand=(38, 11), sword=52, hand_back=(-76, 8), shield_up=0.5,
                cape=(0.34, t, 0.5), legs=(0.3, 0.12, -0.34, -0.14))


def walk_elite(i):
    t = _t(i, 6)
    legs = []
    for ph in (t, t + math.pi):
        th = 0.7 * math.sin(ph)
        legs += [th, th - (0.1 + 0.6 * max(0, math.sin(ph + 1.9)))]
    return pose(lean=0.2, crouch=1.5, legs=tuple(legs), hand=(40, 11), sword=48,
                hand_back=(-78, 8), cape=(0.42, t, 0.8), shift=(1.5 * math.sin(t), 0))


ATTACK_ELITE = [
    pose(lean=-0.16, crouch=2.5, hand=(120, 11), sword=150, legs=(0.5, 0.15, -0.5, -0.5), shield_up=-2),
    pose(lean=-0.3, crouch=3.5, hand=(132, 12), sword=165, legs=(0.55, 0.15, -0.55, -0.55), shield_up=-3),
    pose(lean=0.42, crouch=0.5, hand=(-20, 16), sword=-55, legs=(0.9, 0.35, -0.7, -0.55), smear=(115, -60, 28), shift=(5, 0)),
    pose(lean=0.36, hand=(-38, 14), sword=-70, legs=(0.8, 0.3, -0.6, -0.5), shift=(4, 0)),
    pose(lean=0.12, crouch=1.5, hand=(20, 11), sword=30, legs=(0.35, 0.12, -0.3, -0.28), shift=(2, 0)),
]

# ---- the boss: a heavy tyrant. Deep slow breath, billowing cape, wide planted stance, stomping march.
def idle_boss(i):
    t = _t(i, 4)
    return pose(breath=1.7 * (0.5 - 0.5 * math.cos(t)), lean=0.03 * math.sin(t + 0.5),
                shift=(1.6 * math.sin(t * 0.5), 0), tilt=0.08 * math.sin(t),
                hand=(18, 12), sword=95, hand_back=(-64, 10),
                cape=(0.5, t, 2.5 + 1.2 * math.sin(t)), legs=(0.3, 0.1, -0.35, -0.12))


def walk_boss(i):
    t = _t(i, 6)
    legs = []
    for ph in (t, t + math.pi):
        th = 0.75 * math.sin(ph)
        legs += [th, th - (0.05 + 0.5 * max(0, math.sin(ph + 1.9)))]
    return pose(lean=0.12, legs=tuple(legs), hand=(30, 12), sword=80 + 8 * math.sin(t),
                hand_back=(-56, 10), cape=(0.55, t, 1.5), shift=(2 * math.sin(t), 0))


ATTACK_BOSS = [
    pose(lean=-0.2, hand=(120, 14), sword=150, legs=(0.4, 0.15, -0.45, -0.4)),
    pose(lean=-0.34, hand=(140, 15), sword=168, legs=(0.45, 0.15, -0.5, -0.45), crouch=2),
    pose(lean=0.5, hand=(0, 17), sword=-8, legs=(1.0, 0.4, -0.75, -0.6), crouch=3, smear=(120, -50, 34), shift=(6, 0)),
    pose(lean=0.44, hand=(-20, 15), sword=-25, legs=(0.9, 0.35, -0.7, -0.55), crouch=2.5, shift=(5, 0)),
    pose(lean=0.14, hand=(25, 13), sword=60, legs=(0.35, 0.12, -0.35, -0.3), shift=(2, 0)),
]

# ---- the witch: a hex weaver. She glides, her orb pulses and the staff sways on its own.
def idle_witch(i):
    t = _t(i, 4)
    return pose(lean=0.06 * math.sin(t), hover=2.5 + 1.8 * math.sin(t), sway=math.sin(t) * 2,
                hand=(25 + 8 * math.sin(t + 1), 10), staff=72 + 12 * math.sin(t * 0.5 + 1),
                orb=1.0 + 0.35 * (0.5 - 0.5 * math.cos(t)))


def walk_witch(i):
    t = _t(i, 6)
    return pose(hover=2.5 + math.sin(t) * 2, sway=math.sin(t) * 3, lean=0.1, hand=(25, 10),
                staff=80 + 8 * math.sin(t), orb=1.1 + 0.15 * math.sin(t * 2))


WITCH_ATTACK = [
    dict(lean=-0.1, hand=(70, 10), staff=100, orb=1.0), dict(lean=-0.2, hand=(95, 11), staff=115, orb=1.4),
    dict(lean=-0.25, hand=(110, 11), staff=125, orb=2.0), dict(lean=0.2, hand=(20, 12), staff=45, orb=1.5), dict(lean=0.05, hand=(40, 10), staff=75, orb=0.9),
]


def hurt_h(i):
    return [pose(lean=-0.3, tilt=-0.2, hand=(40, 11), sword=60, legs=(0.3, 0.2, -0.3, -0.4), shift=(-2, 0)),
            pose(lean=-0.45, tilt=-0.3, hand=(55, 10), sword=80, legs=(0.4, 0.3, -0.2, -0.4), shift=(-3, 0))][i]


def death_h(i):
    return [
        pose(lean=-0.35, tilt=-0.2, hand=(45, 11), sword=70, legs=(0.3, 0.2, -0.25, -0.4), shift=(-2, 0)),
        pose(lean=-0.6, crouch=5, hand=(70, 11), sword=95, legs=(0.9, -0.7, 0.4, -0.9), shift=(-4, 0)),
        pose(lean=-0.5, crouch=9, hand=(-60, 11), sword=-80, legs=(1.4, -1.4, 0.9, -1.5), shift=(-4, 0), drop=True),
        pose(rot=-0.9, ground=False, lean=-0.1, hand=(80, 11), sword=100, shift=(-10, -8), drop=True),
        pose(rot=-1.5, ground=False, shift=(-4, -6), drop=True),
        pose(rot=-1.55, ground=False, shift=(-4, -6), drop=True),
    ][i]


def witch_death(i):
    return [dict(lean=-0.3, hover=1), dict(lean=-0.5, hover=0, sway=-3), dict(lean=-0.8, hover=-1, sway=-5),
            dict(lean=-1.2, hover=-3, sway=-7), dict(lean=-1.45, hover=-6, sway=-9), dict(lean=-1.55, hover=-7, sway=-10)][i]


def witch_pose(**kw):
    p = pose(**kw)
    return p


def render(name, p):
    """-> rows: idle, walk, attack, hurt, death   (frames x RGBA arrays)"""
    cols, pal = palette_for(name)
    boss = name == 'boss'
    cell, origin = (BOSS_CELL, BOSS_ORIGIN) if boss else (CELL, ORIGIN)
    tier = {3: 1, 2: 2, 1: 3}[p]
    plan = [('idle', 4), ('walk', 6), ('attack', 5), ('hurt', 2), ('death', 6)]
    humanoid = {
        'footman': {'idle': idle_footman, 'walk': walk_footman, 'attack': lambda j: ATTACK_FOOTMAN[j]},
        'royal': {'idle': idle_royal, 'walk': walk_royal, 'attack': lambda j: ATTACK_ROYAL[j]},
        'elite': {'idle': idle_elite, 'walk': walk_elite, 'attack': lambda j: ATTACK_ELITE[j]},
        'boss': {'idle': idle_boss, 'walk': walk_boss, 'attack': lambda j: ATTACK_BOSS[j]},
    }
    rows = []
    for kind, n in plan:
        row = []
        for i in range(n):
            P = Painter(cell, p, origin, pal, OUTLINE)
            if name == 'witch':
                if kind == 'idle':
                    ps = idle_witch(i)
                elif kind == 'walk':
                    ps = walk_witch(i)
                elif kind == 'attack':
                    ps = pose(**WITCH_ATTACK[i])
                elif kind == 'hurt':
                    ps = pose(lean=-0.25 - 0.1 * i, hover=1, sway=-2 * i, hand=(50, 10), staff=95)
                else:
                    ps = pose(**witch_death(i))
                P.rot = 0
                draw_witch(P, cols, ps, tier)
            else:
                s = STYLES[name]
                ps = humanoid[name].get(kind, {'hurt': hurt_h, 'death': death_h}[kind] if kind in ('hurt', 'death') else None)(i)
                P.scale = s['scale']
                P.rot = ps['rot']
                P.shift = ps['shift']
                draw_humanoid(P, cols, ps, s, tier)
            row.append(P.finish())
        rows.append(row)
    return rows
