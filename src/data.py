# Stats for the hero, weapons and enemies.
# The hero keeps the same body size at every stage. Evolving makes him stronger
# (health, stamina, damage, speed) and changes the colours of his cape and trim.

HERO_SIZE = (28, 46)

EVOLUTION_STAGES = [
    {"name": "The Exile", "cores_required": 0, "max_health": 100, "max_stamina": 100, "damage_mult": 1.0, "speed_mult": 1.0},
    {"name": "The Wanderer", "cores_required": 5, "max_health": 140, "max_stamina": 120, "damage_mult": 1.3, "speed_mult": 1.05},
    {"name": "The Reclaimer", "cores_required": 12, "max_health": 190, "max_stamina": 150, "damage_mult": 1.7, "speed_mult": 1.1},
    {"name": "The Heir Ascendant", "cores_required": 20, "max_health": 260, "max_stamina": 200, "damage_mult": 2.3, "speed_mult": 1.2},
]

# "icon" is the position of the weapon in the icon sheet (static/assets/art/weapons_t*.png)
WEAPONS = {
    "gladius_voltaic": {"display_name": "Gladius", "damage": 14, "range": 46, "cooldown": 300, "color": "#8ec8ff", "icon": 0},
    "pilum_rocketa": {"display_name": "Pilum", "damage": 22, "range": 70, "cooldown": 600, "color": "#ff9a50", "icon": 1},
    "pugio_sparkspike": {"display_name": "Pugio", "damage": 9, "range": 30, "cooldown": 180, "color": "#c8a0ff", "icon": 2},
    "hasta_longwire": {"display_name": "Hasta", "damage": 17, "range": 60, "cooldown": 400, "color": "#7ae0c8", "icon": 3},
    "falx_rustbite": {"display_name": "Falx", "damage": 12, "range": 40, "cooldown": 260, "color": "#d8d8e0", "icon": 4},
    "securis_ashborn": {"display_name": "Securis", "damage": 24, "range": 50, "cooldown": 650, "color": "#e06060", "icon": 5},
    "bipennis_warbreaker": {"display_name": "Bipennis", "damage": 20, "range": 50, "cooldown": 550, "color": "#f0f0f4", "icon": 6},
}
DEFAULT_WEAPON = "gladius_voltaic"

# "art" is the sprite sheet name (static/assets/art/foe_<art>_t<tier>.png)
ENEMY_TYPES = {
    "low_level_knight": {
        "display_name": "Footman", "art": "footman", "size": (30, 46),
        "max_health": 40, "damage": 8, "speed": 1.4, "detect_range": 160, "attack_range": 34,
        "attack_cooldown": 900, "windup": 380, "ranged": False,
    },
    "royal_knight": {
        "display_name": "Royal Knight", "art": "royal", "size": (34, 56),
        "max_health": 90, "damage": 14, "speed": 1.1, "detect_range": 200, "attack_range": 40,
        "attack_cooldown": 1100, "windup": 380, "ranged": False,
    },
    "royal_knight_2": {
        "display_name": "Elite Knight", "art": "elite", "size": (36, 58),
        "max_health": 130, "damage": 18, "speed": 1.3, "detect_range": 220, "attack_range": 42,
        "attack_cooldown": 950, "windup": 380, "ranged": False,
    },
    "witch": {
        "display_name": "Witch", "art": "witch", "size": (28, 46),
        "max_health": 55, "damage": 12, "speed": 0.8, "detect_range": 260, "attack_range": 240,
        "attack_cooldown": 1500, "windup": 450, "ranged": True, "projectile_speed": 5, "projectile_color": "#a45af0",
    },
}
