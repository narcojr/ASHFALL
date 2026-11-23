"""
level_generator.py
-------------------
Builds an infinite sequence of levels. Level 1 is the hand-crafted
INTRO_LEVEL_LAYOUT (see data.py) so new players get a curated start; every
level after that is procedurally generated here, and gets harder as
`level_number` rises:

  - longer levels, more enemies
  - enemy health/damage/speed scaled up (compounding per level)
  - tougher enemy types become more common in the random mix
  - jumps get wider and platform heights more varied
  - chests are more likely to be locked (costs coins to open)
  - the ground/platform texture rotates through 3 stone themes

No seed is fixed, so calling generate() twice produces two different
layouts - "every level is unique" - but you can pass an explicit seed if
you ever want a reproducible layout (e.g. for testing).
"""

import random
from src.settings import GROUND_Y
from src.data import DIFFICULTY, ENEMY_TYPES, WEAPONS, STONE_THEMES, enemy_weights_for_level


def _scaled(base, growth, level_number, cap=None):
    value = base + growth * (level_number - 1)
    if cap is not None:
        value = min(value, cap)
    return value


def enemy_scale_for_level(level_number):
    """Compounding stat multipliers applied to every enemy on this level."""
    d = DIFFICULTY
    n = max(0, level_number - 1)
    return {
        "health": (1 + d["enemy_health_growth"]) ** n,
        "damage": (1 + d["enemy_damage_growth"]) ** n,
        "speed": min(d["max_speed_mult"], (1 + d["enemy_speed_growth"]) ** n),
    }


def generate(level_number, seed=None):
    rng = random.Random(seed) if seed is not None else random.Random()
    d = DIFFICULTY

    level_length = _scaled(d["base_level_length"], d["length_growth_per_level"],
                            level_number, d["max_level_length"])
    level_end_x = int(280 + level_length)

    gap_max = _scaled(d["gap_max"], d["gap_growth_per_level"], level_number, d["gap_max_cap"])
    height_variance = _scaled(d["height_variance_base"], d["height_variance_growth"],
                               level_number, d["height_variance_cap"])

    # ---------------------------------------------------- platforms
    platforms = []
    x = 320
    y = GROUND_Y - 120
    min_y, max_y = 260, GROUND_Y - 100
    while x < level_end_x - 250:
        width = rng.randint(120, 220)
        platforms.append((x, int(y), width, 20))
        x += width + rng.randint(int(d["gap_min"]), int(gap_max))
        y += rng.uniform(-height_variance, height_variance)
        y = max(min_y, min(max_y, y))

    # ---------------------------------------------------- pixel cores
    core_count = round(_scaled(d["pixel_cores_base"], d["pixel_cores_growth"], level_number))
    pixel_cores = []
    for _ in range(core_count):
        if platforms and rng.random() < 0.75:
            plat = rng.choice(platforms)
            px = rng.randint(plat[0] + 10, plat[0] + plat[2] - 10)
            py = plat[1] - rng.randint(50, 90)
        else:
            px = rng.randint(320, level_end_x - 100)
            py = GROUND_Y - rng.randint(60, 110)
        pixel_cores.append((px, py))

    # ---------------------------------------------------- coins
    coin_count = round(_scaled(d["coin_count_base"], d["coin_count_growth"], level_number))
    coins = [(rng.randint(320, level_end_x - 100), GROUND_Y - 40) for _ in range(coin_count)]

    # ---------------------------------------------------- chests
    chest_count = max(1, round(_scaled(d["chest_count_base"], d["chest_count_growth"], level_number)))
    locked_chance = min(d["locked_chest_max_chance"],
                         d["locked_chest_chance_start"] + d["locked_chest_chance_growth"] * (level_number - 1))
    chests = []
    for _ in range(chest_count):
        cx = rng.randint(400, level_end_x - 150)
        locked = rng.random() < locked_chance
        chests.append((cx, GROUND_Y - 46, locked))

    # ---------------------------------------------------- lore books & weapons
    lore_books = []
    if rng.random() < d["lore_book_chance"]:
        lore_books.append((rng.randint(400, level_end_x - 150), GROUND_Y - 44))

    weapon_pickups = []
    if rng.random() < d["weapon_pickup_chance"]:
        weapon_key = rng.choice(list(WEAPONS.keys()))
        weapon_pickups.append((rng.randint(400, level_end_x - 150), GROUND_Y - 40, weapon_key))

    # ---------------------------------------------------- decorations (visual only)
    deco_count = round(_scaled(d["decoration_count_base"], d["decoration_count_growth"], level_number))
    decorations = []
    for _ in range(deco_count):
        kind = rng.choice(["campfire", "tombstone"])
        # Decoration anchors its sprite so its bottom sits on this y value,
        # so pass the ground line itself (not an already-offset height).
        decorations.append((rng.randint(150, level_end_x - 150), GROUND_Y, kind))

    # ---------------------------------------------------- enemies
    enemy_count = min(d["max_enemy_count"],
                       round(_scaled(d["base_enemy_count"], d["enemy_growth_per_level"], level_number)))
    weights = enemy_weights_for_level(level_number)
    types = list(weights.keys())
    weight_values = [weights[t] for t in types]

    enemies = []
    for _ in range(enemy_count):
        etype = rng.choices(types, weights=weight_values, k=1)[0]
        ex = rng.randint(420, level_end_x - 150)
        enemy_h = ENEMY_TYPES[etype]["size"][1]
        if platforms and rng.random() < 0.4:
            plat = rng.choice(platforms)
            ex = rng.randint(plat[0], plat[0] + plat[2] - 20)
            ey = plat[1] - enemy_h
        else:
            ey = GROUND_Y - enemy_h
        enemies.append((ex, ey, etype))

    stone_theme = (level_number - 1) % len(STONE_THEMES)

    return {
        "platforms": platforms,
        "pixel_cores": pixel_cores,
        "coins": coins,
        "chests": chests,
        "lore_books": lore_books,
        "weapon_pickups": weapon_pickups,
        "decorations": decorations,
        "enemies": enemies,
        "level_end_x": level_end_x,
        "stone_theme": stone_theme,
        "enemy_scale": enemy_scale_for_level(level_number),
    }
