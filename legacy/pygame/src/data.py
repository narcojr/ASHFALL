"""
data.py
-------
The design spreadsheet. Evolution stages, weapons, enemy base stats, art
filenames, and difficulty-scaling knobs all live here as plain data so you
can rebalance the game (or add a weapon/enemy/level theme) without ever
touching the class files.
"""

from src.settings import COLOR_GOLD, COLOR_BLUE, COLOR_PURPLE, COLOR_WHITE

# ---------------------------------------------------------- PIXEL EVOLUTION
EVOLUTION_STAGES = [
    {
        "name": "The Exile",
        "cores_required": 0,
        "size": (28, 40),
        "color": (110, 110, 120),
        "max_health": 100,
        "max_stamina": 100,
        "damage_mult": 1.0,
        "speed_mult": 1.0,
        "description": "Small, blocky sprite with basic abilities.",
    },
    {
        "name": "The Wanderer",
        "cores_required": 5,
        "size": (32, 46),
        "color": (90, 130, 150),
        "max_health": 140,
        "max_stamina": 120,
        "damage_mult": 1.3,
        "speed_mult": 1.05,
        "description": "More detailed appearance, stronger attacks, improved armor.",
    },
    {
        "name": "The Reclaimer",
        "cores_required": 12,
        "size": (36, 52),
        "color": (200, 170, 70),
        "max_health": 190,
        "max_stamina": 150,
        "damage_mult": 1.7,
        "speed_mult": 1.1,
        "description": "High-definition pixel art, advanced skills, legendary equipment.",
    },
    {
        "name": "The Heir Ascendant",
        "cores_required": 20,
        "size": (40, 58),
        "color": (230, 60, 50),
        "max_health": 260,
        "max_stamina": 200,
        "damage_mult": 2.3,
        "speed_mult": 1.2,
        "description": "Nearly lifelike visuals - unmatched power, ready for the Dominion.",
    },
]

# ---------------------------------------------------------------- WEAPONS
# Every weapon icon below is real pixel-art dropped into assets/images/.
# `ranged`: True means attacking fires a Projectile instead of a melee swing.
WEAPONS = {
    "gladius_voltaic": {
        "display_name": "Gladius Voltaic",
        "desc": "rebar + battery",
        "damage": 14, "range": 46, "cooldown": 300,
        "color": COLOR_BLUE, "icon": "weapon_sword_silver.png", "ranged": False,
    },
    "pilum_rocketa": {
        "display_name": "Pilum Rocketa",
        "desc": "javelin + rocket tube",
        "damage": 22, "range": 70, "cooldown": 600,
        "color": (210, 90, 40), "icon": "weapon_spear_fire.png", "ranged": False,
    },
    "pugio_sparkspike": {
        "display_name": "Pugio Sparkspike",
        "desc": "dagger + igniter",
        "damage": 9, "range": 30, "cooldown": 180,
        "color": COLOR_PURPLE, "icon": "weapon_dagger_purple.png", "ranged": False,
    },
    "hasta_longwire": {
        "display_name": "Hasta Longwire",
        "desc": "spear + live wire",
        "damage": 17, "range": 60, "cooldown": 400,
        "color": (60, 160, 150), "icon": "weapon_trident_teal.png", "ranged": False,
    },
    "falx_rustbite": {
        "display_name": "Falx Rustbite",
        "desc": "leaf-spring blade",
        "damage": 12, "range": 40, "cooldown": 260,
        "color": (60, 60, 65), "icon": "weapon_scythe_black.png", "ranged": False,
    },
    "securis_ashborn": {
        "display_name": "Securis Ashborn",
        "desc": "reclaimed battle axe",
        "damage": 24, "range": 50, "cooldown": 650,
        "color": (150, 40, 40), "icon": "weapon_axe_blood.png", "ranged": False,
    },
    "bipennis_warbreaker": {
        "display_name": "Bipennis Warbreaker",
        "desc": "twin-headed scrap axe",
        "damage": 20, "range": 50, "cooldown": 550,
        "color": (200, 200, 205), "icon": "weapon_axe_silver.png", "ranged": False,
    },
    "arcus_scavenger": {
        "display_name": "Arcus Scavenger",
        "desc": "salvaged hunting bow",
        "damage": 11, "range": 320, "cooldown": 500,
        "color": (170, 130, 90), "icon": "weapon_bow.png", "ranged": True,
        "projectile_speed": 9,
    },
}

DEFAULT_WEAPON = "gladius_voltaic"

# ---------------------------------------------------------------- ENEMIES
# Base stats only - LevelGenerator scales health/damage/speed up as the
# player advances through levels (see DIFFICULTY below), so you never need
# to hand-tune these per level.
ENEMY_TYPES = {
    "low_level_knight": {
        "display_name": "Low Level Knight",
        "size": (30, 46), "color": (150, 150, 155),
        "max_health": 40, "damage": 8, "speed": 1.4,
        "detect_range": 160, "attack_range": 34, "attack_cooldown": 900,
        "ranged": False, "image": "enemy_low_level_knight.png", "tint": None,
    },
    "royal_knight": {
        "display_name": "The Royal Knight",
        "size": (34, 56), "color": (60, 110, 100),
        "max_health": 90, "damage": 14, "speed": 1.1,
        "detect_range": 200, "attack_range": 40, "attack_cooldown": 1100,
        "ranged": False, "image": "enemy_royal_knight.png", "tint": None,
    },
    "royal_knight_2": {
        "display_name": "The Royal Knight II",
        "size": (36, 58), "color": (50, 130, 120),
        "max_health": 130, "damage": 18, "speed": 1.3,
        "detect_range": 220, "attack_range": 42, "attack_cooldown": 950,
        # same art as the Royal Knight, palette-swapped emerald so it
        # reads as a tougher elite variant without needing new art.
        "ranged": False, "image": "enemy_royal_knight.png", "tint": (120, 220, 170),
    },
    "witch": {
        "display_name": "The Witch",
        "size": (28, 46), "color": (90, 90, 200),
        "max_health": 55, "damage": 12, "speed": 0.8,
        "detect_range": 260, "attack_range": 240, "attack_cooldown": 1500,
        "ranged": True, "projectile_speed": 5, "projectile_color": (160, 60, 200),
        "image": "enemy_witch.png", "tint": None,
    },
}

# The Dominion (final-boss-style unit) reuses the Royal Knight art with a
# blood-red palette swap. See enemy.py DominionBoss.
DOMINION_TINT = (255, 90, 70)

# ---------------------------------------------------------------- TERRAIN
# Rotates per level so the world doesn't look the same forever.
STONE_THEMES = [
    {"name": "Cracked Quarry", "ground": "tile_stone_gray.png", "platform": "tile_stone_gray.png"},
    {"name": "Ashfall Ruins", "ground": "tile_brick_gray.png", "platform": "tile_brick_gray.png"},
    {"name": "Midnight Hollow", "ground": "tile_stone_navy.png", "platform": "tile_stone_navy.png"},
]

# ---------------------------------------------------------------- WORLD PROPS
ITEM_ICONS = {
    "pixel_core": None,  # drawn procedurally in items.py (glowing shard)
    "coin": "item_coin_stack.png",
    "lore_book": "item_book_skull.png",
    "lock": "prop_lock.png",
    "campfire": "prop_campfire.png",
    "tombstone": "prop_tombstone.png",
}

# ---------------------------------------------------------------- DIFFICULTY
# Everything LevelGenerator needs to make level N harder than level N-1,
# while still being beatable. Tune these to change the game's pacing.
DIFFICULTY = {
    "base_level_length": 1800,       # px, level 1 length
    "length_growth_per_level": 220,  # px added per level
    "max_level_length": 5200,

    "base_enemy_count": 4,
    "enemy_growth_per_level": 1,     # extra enemies per level
    "max_enemy_count": 22,

    "enemy_health_growth": 0.09,     # +9% enemy max HP per level (compounds)
    "enemy_damage_growth": 0.07,     # +7% enemy damage per level
    "enemy_speed_growth": 0.03,      # +3% enemy speed per level (capped)
    "max_speed_mult": 1.9,

    "pixel_cores_base": 6,
    "pixel_cores_growth": 0.4,       # extra cores per level (rounded)

    "coin_count_base": 2,
    "coin_count_growth": 0.5,

    "chest_count_base": 1,
    "chest_count_growth": 0.25,
    "locked_chest_chance_start": 0.15,   # chance a chest is locked, grows per level
    "locked_chest_chance_growth": 0.03,
    "locked_chest_max_chance": 0.7,

    "lore_book_chance": 0.35,        # chance a level spawns one lore book
    "weapon_pickup_chance": 0.55,    # chance a level spawns one weapon upgrade

    "gap_min": 140, "gap_max": 260,          # horizontal gap between platforms
    "gap_growth_per_level": 4,               # gaps get slightly wider (harder jumps)
    "gap_max_cap": 340,

    "height_variance_base": 90,      # vertical variance between platforms
    "height_variance_growth": 3,
    "height_variance_cap": 170,

    "decoration_count_base": 3,
    "decoration_count_growth": 0.3,
}

# Enemy type weights by "tier" - as the level number rises, weaker enemy
# types become rarer and tougher ones become common. Weights don't need to
# sum to anything in particular; they're relative.
def enemy_weights_for_level(level_number):
    return {
        "low_level_knight": max(1, 10 - level_number),
        "royal_knight": 6 + min(level_number, 10),
        "royal_knight_2": max(0, level_number - 1) * 2,
        "witch": 3 + min(level_number, 8),
    }


# ---------------------------------------------------------------- INTRO LEVEL
# A hand-placed, gentle first level (used for level 1 only) so new players
# get a curated introduction before the procedural generator takes over
# from level 2 onward. Same format LevelGenerator produces.
INTRO_LEVEL_LAYOUT = {
    "platforms": [
        (300, 420, 160, 20), (560, 360, 140, 20), (820, 420, 160, 20),
        (1100, 320, 140, 20), (1380, 420, 160, 20), (1650, 360, 140, 20),
    ],
    "pixel_cores": [
        (330, 380), (620, 320), (860, 380), (1140, 280), (1420, 380), (1690, 320),
        (500, 420), (950, 420),
    ],
    "coins": [(700, 460), (1500, 420)],
    "chests": [(700, 460, False), (1600, 420, False)],
    "lore_books": [],
    "weapon_pickups": [],
    "decorations": [(120, 460, "campfire"), (1750, 460, "tombstone")],
    "enemies": [
        (450, 420, "low_level_knight"), (900, 420, "low_level_knight"),
        (1200, 300, "witch"), (1450, 420, "royal_knight"),
    ],
    "level_end_x": 1850,
    "stone_theme": 0,
}
