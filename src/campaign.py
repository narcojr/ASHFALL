# The three levels of the game. Layouts are generated from fixed seeds, so every player
# gets the same level. validate() checks that every platform can be reached with the
# real jump height.


import random

from src.settings import GRAVITY, GROUND_Y, PLAYER_JUMP_POWER

STEP_H = 80          # height difference between platform rows (a full jump is about 104px)
PLAT_H = 20
SCREEN_W = 960

# meta
LEVELS = [
    {"id": 1, "name": "Frostbound Path", "tagline": "Only basic enemies",
     "theme": "forest", "stone_theme": 0, "seed": 1101, "length": 3400,
     "start_cores": 0, "tier": 1},
    {"id": 2, "name": "Shattered Ruins", "tagline": "Enemies and deadly traps",
     "theme": "ruins", "stone_theme": 1, "seed": 2202, "length": 4200,
     "start_cores": 5, "tier": 2},
    {"id": 3, "name": "The Dominion's Gate", "tagline": "Enemies and the final boss fight",
     "theme": "night", "stone_theme": 2, "seed": 3303, "length": 3300,
     "start_cores": 12, "tier": 3},
]

# Enemy multipliers per level, applied on top of data.ENEMY_TYPES.
ENEMY_SCALE = {
    1: {"health": 0.9, "damage": 0.8, "speed": 1.0},
    2: {"health": 1.1, "damage": 1.0, "speed": 1.05},
    3: {"health": 1.3, "damage": 1.15, "speed": 1.1},
}

# How many of each enemy a level has. Level 1 only has the basic enemy.
ENEMY_PLAN = {
    1: {"low_level_knight": 9},
    2: {"low_level_knight": 4, "royal_knight": 3, "witch": 3},
    3: {"low_level_knight": 2, "royal_knight": 3, "royal_knight_2": 3, "witch": 3},
}
CORES = {1: 10, 2: 12, 3: 12}
COINS = {1: 6, 2: 7, 3: 6}

TRAPS = {
    "spike": {"damage": 14, "height": 16},
    "icicle": {"damage": 18, "trigger": 70, "warn_ms": 450},
    "fire": {"damage": 10, "on_ms": 1400, "off_ms": 1700},
}

BOSS = {
    "name": "The Dominion",
    "size": [58, 86], "art": "boss",
    "max_health": 520,
    "damage": 20,
    "speed": 1.7,
    "intro_ms": 1600,
    "wave_damage": 16,
    "enrage_at": 0.5,
}

DIFFICULTY = {
    "easy":   {"enemy_damage": 0.6, "enemy_health": 0.8},
    "normal": {"enemy_damage": 1.0, "enemy_health": 1.0},
    "hard":   {"enemy_damage": 1.5, "enemy_health": 1.3},
}

LEVEL_WEAPON = {2: "pilum_rocketa", 3: "securis_ashborn"}


# helpers
def _rects_overlap_x(a0, a1, b0, b1, margin=0):
    return a0 - margin < b1 and a1 + margin > b0


def _platform_clusters(rng, x_start, x_end):
    """Ascending/descending runs of platforms, separated by open ground."""
    plats = []
    x = x_start
    while x < x_end - 320:
        count = rng.randint(2, 4)
        tier = 1
        cx = x
        for _ in range(count):
            w = rng.randint(110, 170)
            plats.append([int(cx), GROUND_Y - STEP_H * tier, w, PLAT_H])
            cx += w + rng.randint(50, 85)       # gap small enough to jump
            tier = max(1, min(3, tier + rng.choice([-1, 0, 1, 1])))
        x = cx + rng.randint(380, 560)           # open ground between clusters
    return plats


def _free_ground_spans(platforms, lo, hi, margin=70):
    """Ground x-ranges with no platform overhead (so a jump is never blocked)."""
    blocked = sorted((p[0] - margin, p[0] + p[2] + margin) for p in platforms)
    spans, cur = [], lo
    for b0, b1 in blocked:
        if b0 > cur:
            spans.append((cur, min(b0, hi)))
        cur = max(cur, b1)
    if cur < hi:
        spans.append((cur, hi))
    return [(a, b) for a, b in spans if b - a > 60]


def _pick_spots(rng, spans, count, min_gap, width=0):
    """Random x positions inside free spans, at least min_gap apart."""
    spots = []
    tries = 0
    while len(spots) < count and tries < 800 and spans:
        tries += 1
        a, b = rng.choice(spans)
        if b - a <= width + 10:
            continue
        x = rng.randint(int(a), int(b - width))
        if all(abs(x - s) >= min_gap for s in spots):
            spots.append(x)
    return sorted(spots)


# builder
def build_level(number):
    meta = next((m for m in LEVELS if m["id"] == number), None)
    if meta is None:
        raise ValueError(f"unknown level {number}")
    rng = random.Random(meta["seed"])

    main_end = meta["length"]
    is_boss = number == 3
    end_x = None if is_boss else main_end
    arena = None
    if is_boss:
        arena = {"start": main_end + 120, "end": main_end + 120 + SCREEN_W}
        width = arena["end"] + 120
    else:
        width = main_end + 260

    # ---- platforms (never inside the boss arena or the safe start zone)
    platforms = _platform_clusters(rng, 380, main_end - 120)
    if is_boss:
        platforms += [[arena["start"] + 130, GROUND_Y - STEP_H, 140, PLAT_H],
                      [arena["end"] - 270, GROUND_Y - STEP_H, 140, PLAT_H]]

    # ---- pixel cores: mostly on platforms, the rest on ground
    cores = []
    plat_candidates = [p for p in platforms if p[0] > 380 and (not arena or p[0] < arena["start"])]
    rng.shuffle(plat_candidates)
    for p in plat_candidates[: int(CORES[number] * 0.7)]:
        cores.append([p[0] + p[2] // 2 - 7, p[1] - 34])
    spans = _free_ground_spans(platforms, 420, main_end - 100)
    for x in _pick_spots(rng, spans, CORES[number] - len(cores), 150):
        cores.append([x, GROUND_Y - 44])
    while len(cores) < CORES[number]:           # ultra-safe fallback
        cores.append([500 + 90 * len(cores), GROUND_Y - 44])

    # ---- hazards (level 2 only)
    spikes, icicles, fires = [], [], []
    hazard_x = []
    if number == 2:
        def place(count, min_gap, width, check_platforms):
            out, tries = [], 0
            while len(out) < count and tries < 3000:
                tries += 1
                x = rng.randint(620, main_end - 260)
                if any(abs(x - h) < min_gap for h in hazard_x):
                    continue
                if check_platforms and any(_rects_overlap_x(x, x + width, p[0], p[0] + p[2], 56)
                                           for p in platforms):
                    continue
                out.append(x)
                hazard_x.append(x)
            return sorted(out)
        fires = [[x, rng.randint(0, 2800)] for x in place(3, 150, 40, True)]
        spikes = [[x, rng.choice([40, 52, 64])] for x in place(4, 150, 80, True)]
        icicles = [[x] for x in place(5, 160, 30, False)]

    # ---- enemies
    enemies = []
    used = []
    kinds = []
    for kind, n in ENEMY_PLAN[number].items():
        kinds += [kind] * n
    rng.shuffle(kinds)
    from src.data import ENEMY_TYPES
    lo, hi = 640, (arena["start"] - 260 if arena else main_end - 220)
    attempts = 0
    for kind in kinds:
        eh = ENEMY_TYPES[kind]["size"][1]
        placed = False
        while not placed and attempts < 4000:
            attempts += 1
            x = rng.randint(lo, hi)
            on_plat = None
            if rng.random() < 0.3:
                cand = [p for p in platforms if p[2] >= 120 and lo < p[0] < hi]
                if cand:
                    on_plat = rng.choice(cand)
                    x = rng.randint(on_plat[0] + 30, on_plat[0] + on_plat[2] - 50)
            if any(abs(x - u) < 170 for u in used):
                continue
            if any(abs(x - h) < 90 for h in hazard_x):
                continue
            if on_plat is None and any(_rects_overlap_x(x, x + 30, p[0], p[0] + p[2], 20) and p[1] > GROUND_Y - STEP_H * 1.5
                                        for p in platforms):
                pass  # standing under a low platform is fine (they patrol on the ground)
            y = (on_plat[1] if on_plat else GROUND_Y) - eh
            enemies.append([x, y, kind])
            used.append(x)
            placed = True
        if not placed:
            raise RuntimeError("could not place enemies")

    # ---- coins, chests, books, weapon, decoration
    coins = [[x, GROUND_Y - 26] for x in _pick_spots(rng, spans, COINS[number], 150)]
    chests = []
    for x in _pick_spots(rng, spans, 2, 700):
        chests.append([x, GROUND_Y - 28, number > 1 and rng.random() < 0.4])
    if is_boss:  # one guaranteed free heal right before the gate
        chests.append([arena["start"] - 220, GROUND_Y - 28, False])
    books = [[x, GROUND_Y - 30] for x in _pick_spots(rng, spans, 1, 100)] if number >= 2 else []
    weapons = []
    if number in LEVEL_WEAPON:
        weapons.append([560, GROUND_Y - 36, LEVEL_WEAPON[number]])

    decor_kinds = ["rock", "rock_small", "tree", "ice_plant", "sign", "fence", "pillar", "tombstone", "lantern"]
    if number == 1:
        decor_kinds = ["rock", "rock_small", "tree", "ice_plant", "sign", "fence"]
    decor = []
    for x in range(160, width - 100, 190):
        if rng.random() < 0.72:
            decor.append([x + rng.randint(-40, 40), rng.choice(decor_kinds)])
    rest = [[arena["start"] - 120]] if is_boss else []

    layout = {
        "id": number, "name": meta["name"], "tagline": meta["tagline"],
        "theme": meta["theme"], "stone_theme": meta["stone_theme"], "tier": meta["tier"],
        "width": width, "end_x": end_x, "arena": arena,
        "start": {"x": 100, "cores": meta["start_cores"],
                  "weapon": "gladius_voltaic"},
        "platforms": platforms, "cores": cores, "coins": coins, "chests": chests,
        "books": books, "weapons": weapons, "decor": decor, "rest": rest,
        "enemies": enemies, "spikes": spikes, "icicles": icicles, "fires": fires,
        "enemy_scale": ENEMY_SCALE[number],
        "boss": {"x": arena["end"] - 220, "y": GROUND_Y - BOSS["size"][1]} if is_boss else None,
    }
    problems = validate(layout)
    if problems:
        raise RuntimeError(f"level {number} failed validation: {problems}")
    return layout


# validation
def max_jump_height():
    """Peak height of a full jump, stepping the same way the game does
    (gravity is applied, then the entity moves)."""
    v, h, peak = PLAYER_JUMP_POWER, 0.0, 0.0
    while True:
        v += GRAVITY
        h -= v
        peak = max(peak, h)
        if v >= 0:
            return peak


def validate(layout):
    """Return a list of human-readable problems (empty list == level is sound)."""
    problems = []
    jump = max_jump_height()
    if jump < STEP_H + 10:
        problems.append(f"jump height {jump:.0f} too low for tier {STEP_H}")
    plats = layout["platforms"]
    width = layout["width"]

    # reachability: BFS from the ground through platforms
    reach = set()
    frontier = [i for i, p in enumerate(plats) if GROUND_Y - p[1] <= jump - 12]
    reach.update(frontier)
    while frontier:
        nxt = []
        for i in frontier:
            a = plats[i]
            for j, b in enumerate(plats):
                if j in reach:
                    continue
                gap = max(b[0] - (a[0] + a[2]), a[0] - (b[0] + b[2]))
                if gap <= 100 and (a[1] - b[1]) <= jump - 12:
                    reach.add(j)
                    nxt.append(j)
        frontier = nxt
    for i, p in enumerate(plats):
        if i not in reach:
            problems.append(f"platform {p} unreachable")
        if p[0] < 0 or p[0] + p[2] > width:
            problems.append(f"platform {p} out of bounds")

    for x, y in layout["cores"]:
        if not (0 <= x <= width):
            problems.append(f"core {x},{y} out of bounds")
        on = [p for p in plats if p[0] - 10 <= x <= p[0] + p[2] + 10 and p[1] - 120 < y < p[1]]
        if not on and y < GROUND_Y - 100:
            problems.append(f"core {x},{y} floating")
    for name in ("spikes", "fires"):
        for h in layout[name]:
            for p in plats:
                if _rects_overlap_x(h[0], h[0] + 70, p[0], p[0] + p[2], 0):
                    problems.append(f"{name} {h} under platform {p}")
    for e in layout["enemies"]:
        if not (0 < e[0] < width):
            problems.append(f"enemy {e} out of bounds")
    kinds = {e[2] for e in layout["enemies"]}
    if layout["id"] == 1 and kinds != {"low_level_knight"}:
        problems.append("level 1 must only contain basic enemies")
    if layout["id"] == 2 and not (layout["spikes"] and layout["icicles"] and layout["fires"]):
        problems.append("level 2 must contain traps")
    if layout["id"] != 2 and (layout["spikes"] or layout["icicles"] or layout["fires"]):
        problems.append("traps are only in level 2")
    if layout["id"] == 3 and not layout["boss"]:
        problems.append("level 3 needs a boss")
    return problems
