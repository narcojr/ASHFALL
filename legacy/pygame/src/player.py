"""
player.py
---------
The Heir - the exiled rightful successor of the Dominion, raised in the
wasteland. This class handles input, movement, attacking, and holds the
PixelEvolutionSystem that grows the character over the course of the game.
"""

import pygame
from src.entity import Entity
from src.evolution import PixelEvolutionSystem
from src import assets
from src.settings import (
    PLAYER_START_X, PLAYER_START_Y, PLAYER_MOVE_SPEED, PLAYER_JUMP_POWER,
    PLAYER_ATTACK_COOLDOWN, PLAYER_HURT_COOLDOWN, PLAYER_STAMINA_REGEN,
    ATTACK_STAMINA_COST, KEY_LEFT, KEY_RIGHT, KEY_JUMP, KEY_ATTACK,
)
from src.data import EVOLUTION_STAGES, WEAPONS, DEFAULT_WEAPON
from src.items import Projectile


class Player(Entity):
    def __init__(self):
        stage0 = EVOLUTION_STAGES[0]
        w, h = stage0["size"]
        super().__init__(PLAYER_START_X, PLAYER_START_Y, w, h, stage0["color"], stage0["max_health"])
        # Drop a PNG named "player_stage_0.png" (etc, matching stage index)
        # into assets/images/ and it will be used automatically instead of
        # the placeholder block. See evolution.py for the stage-swap logic.
        self.image = assets.load_image("player_stage_0.png", (w, h), stage0["color"])

        self.max_stamina = stage0["max_stamina"]
        self.stamina = self.max_stamina
        self.damage_mult = stage0["damage_mult"]
        self.speed_mult = stage0["speed_mult"]

        self.weapon_key = DEFAULT_WEAPON
        self.pixel_core_count = 0
        self.coins = 0

        self._attack_timer = 0
        self._hurt_timer = 0
        self.is_attacking = False
        self.attack_hitbox = None
        self.pending_projectile = None
        self.on_evolve_flash_ms = 0

        # The evolution system is attached last, since it needs a fully
        # constructed player to read/modify.
        self.evolution = PixelEvolutionSystem(self)

    # ---------------------------------------------------------- input
    def handle_input(self, keys, dt_ms):
        move = 0
        if any(keys[k] for k in KEY_LEFT):
            move -= 1
        if any(keys[k] for k in KEY_RIGHT):
            move += 1

        speed = PLAYER_MOVE_SPEED * self.speed_mult
        self.vel_x = move * speed
        if move != 0:
            self.facing_right = move > 0

        if any(keys[k] for k in KEY_JUMP) and self.on_ground:
            self.vel_y = PLAYER_JUMP_POWER

        if any(keys[k] for k in KEY_ATTACK):
            self.try_attack()

    def try_attack(self):
        if self._attack_timer > 0:
            return
        if self.stamina < ATTACK_STAMINA_COST:
            return

        weapon = WEAPONS[self.weapon_key]
        self._attack_timer = max(PLAYER_ATTACK_COOLDOWN, weapon["cooldown"])
        self.stamina -= ATTACK_STAMINA_COST
        self.is_attacking = True

        if weapon.get("ranged"):
            direction = 1 if self.facing_right else -1
            self.pending_projectile = Projectile(
                self.rect.centerx, self.rect.centery, direction,
                weapon.get("projectile_speed", 9), self.current_weapon_damage(),
                weapon["color"], owner="player",
            )
            self.attack_hitbox = None
            return

        rng = weapon["range"]
        if self.facing_right:
            self.attack_hitbox = pygame.Rect(self.rect.right, self.rect.y, rng, self.rect.height)
        else:
            self.attack_hitbox = pygame.Rect(self.rect.left - rng, self.rect.y, rng, self.rect.height)

    def take_pending_projectile(self):
        p = self.pending_projectile
        self.pending_projectile = None
        return p

    def current_weapon_damage(self):
        weapon = WEAPONS[self.weapon_key]
        return weapon["damage"] * self.damage_mult

    def equip_weapon(self, weapon_key):
        if weapon_key in WEAPONS:
            self.weapon_key = weapon_key

    @property
    def weapon_display_name(self):
        return WEAPONS[self.weapon_key]["display_name"]

    # ---------------------------------------------------------- pickups
    def collect_pixel_core(self):
        self.pixel_core_count += 1
        self.evolution.collect_core()

    def collect_coins(self, amount):
        self.coins += amount

    def take_damage(self, amount):
        if self._hurt_timer > 0:
            return  # invulnerable right after being hit
        super().take_damage(amount)
        self._hurt_timer = PLAYER_HURT_COOLDOWN

    # ---------------------------------------------------------- update
    def update(self, dt_ms, platforms):
        self.apply_gravity()
        self.move_and_collide(platforms)

        # stamina regen
        self.stamina = min(self.max_stamina, self.stamina + PLAYER_STAMINA_REGEN)

        # timers
        if self._attack_timer > 0:
            self._attack_timer -= dt_ms
        else:
            self.is_attacking = False
            self.attack_hitbox = None

        if self._hurt_timer > 0:
            self._hurt_timer -= dt_ms

        if self.on_evolve_flash_ms > 0:
            self.on_evolve_flash_ms -= dt_ms

    @property
    def is_invulnerable(self):
        return self._hurt_timer > 0

    # ---------------------------------------------------------- drawing
    def draw(self, surface, camera):
        super().draw(surface, camera)
        if self.attack_hitbox is not None:
            weapon_color = WEAPONS[self.weapon_key]["color"]
            pygame.draw.rect(surface, weapon_color, camera.apply(self.attack_hitbox), width=2)
