"""
enemy.py
--------
One data-driven Enemy class covers the Low Level Knight, Royal Knight,
Royal Knight II, and the ranged Witch - their differences come from the
ENEMY_TYPES table in data.py, not separate code paths. `health_mult`,
`damage_mult` and `speed_mult` let LevelGenerator scale enemies up as the
player advances through levels without touching this file.

DominionBoss subclasses Enemy for a tougher unit that reuses the Royal
Knight art with a blood-red palette swap, gaining an enrage phase at half
health.
"""

import random
import pygame
from src.entity import Entity
from src.data import ENEMY_TYPES, DOMINION_TINT
from src.items import Projectile
from src import assets

PATROL = "patrol"
CHASE = "chase"
ATTACK = "attack"


class Enemy(Entity):
    def __init__(self, x, y, enemy_type, health_mult=1.0, damage_mult=1.0, speed_mult=1.0):
        cfg = ENEMY_TYPES[enemy_type]
        w, h = cfg["size"]
        max_health = int(cfg["max_health"] * health_mult)
        super().__init__(x, y, w, h, cfg["color"], max_health)

        self.image = assets.load_image(cfg["image"], (w, h), cfg["color"], tint=cfg.get("tint"))

        self.enemy_type = enemy_type
        self.display_name = cfg["display_name"]
        self.damage = cfg["damage"] * damage_mult
        self.speed = cfg["speed"] * speed_mult
        self.detect_range = cfg["detect_range"]
        self.attack_range = cfg["attack_range"]
        self.attack_cooldown = cfg["attack_cooldown"]
        self.ranged = cfg.get("ranged", False)
        self.projectile_speed = cfg.get("projectile_speed", 5)
        self.projectile_color = cfg.get("projectile_color", (200, 60, 200))

        self.state = PATROL
        self.patrol_origin_x = x
        self.patrol_radius = 90
        self.patrol_dir = random.choice([-1, 1])

        self._attack_timer = 0
        self.pending_projectile = None

    # ---------------------------------------------------------- AI
    def update(self, dt_ms, platforms, player):
        if not self.alive:
            return

        dist_x = player.rect.centerx - self.rect.centerx
        abs_dist = abs(dist_x)

        if abs_dist <= self.attack_range:
            self.state = ATTACK
        elif abs_dist <= self.detect_range:
            self.state = CHASE
        else:
            self.state = PATROL

        if self.state == PATROL:
            self._do_patrol()
        elif self.state == CHASE:
            self._do_chase(dist_x)
        elif self.state == ATTACK:
            self.vel_x = 0
            self._do_attack(dist_x, player)

        self.facing_right = dist_x >= 0 if self.state != PATROL else self.facing_right

        self.apply_gravity()
        self.move_and_collide(platforms)

        if self._attack_timer > 0:
            self._attack_timer -= dt_ms

    def _do_patrol(self):
        self.vel_x = self.speed * self.patrol_dir
        self.facing_right = self.patrol_dir > 0
        if abs(self.rect.centerx - self.patrol_origin_x) > self.patrol_radius:
            self.patrol_dir *= -1

    def _do_chase(self, dist_x):
        direction = 1 if dist_x > 0 else -1
        self.vel_x = self.speed * direction

    def _do_attack(self, dist_x, player):
        if self._attack_timer > 0:
            return
        self._attack_timer = self.attack_cooldown

        if self.ranged:
            direction = 1 if dist_x >= 0 else -1
            self.pending_projectile = Projectile(
                self.rect.centerx, self.rect.centery, direction,
                self.projectile_speed, self.damage, self.projectile_color, owner="enemy",
            )
        else:
            player.take_damage(self.damage)

    def take_pending_projectile(self):
        p = self.pending_projectile
        self.pending_projectile = None
        return p

    # ---------------------------------------------------------- drawing
    def draw(self, surface, camera):
        super().draw(surface, camera)
        if self.alive:
            self._draw_health_bar(surface, camera)

    def _draw_health_bar(self, surface, camera):
        bar_w = self.rect.width
        pos = camera.apply(self.rect)
        bar_rect = pygame.Rect(pos.x, pos.y - 8, bar_w, 4)
        pygame.draw.rect(surface, (40, 10, 10), bar_rect)
        fill_rect = pygame.Rect(pos.x, pos.y - 8, int(bar_w * self.health_percent), 4)
        pygame.draw.rect(surface, (200, 40, 40), fill_rect)


class DominionBoss(Enemy):
    """
    The usurper's champion. Reuses the Royal Knight AI and art (palette
    swapped blood-red), but gains an "enrage" phase at half health: faster
    and hits harder. Spawn one manually (see level.py) to gate progress
    every few levels, or drop it in your own boss-arena level.
    """

    def __init__(self, x, y, health_mult=1.0, damage_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, "royal_knight", health_mult, damage_mult, speed_mult)
        w, h = self.rect.width + 6, self.rect.height + 10
        self.image = assets.load_image("enemy_royal_knight.png", (w, h), self.color, tint=DOMINION_TINT)
        self.rect.width, self.rect.height = w, h

        self.display_name = "The Dominion"
        self.max_health = int(self.max_health * 1.8)
        self.health = self.max_health
        self.damage *= 1.6
        self.speed *= 1.2
        self.detect_range += 60
        self.enraged = False

    def update(self, dt_ms, platforms, player):
        if not self.enraged and self.health_percent <= 0.5:
            self.enraged = True
            self.speed *= 1.5
            self.damage *= 1.4
        super().update(dt_ms, platforms, player)
