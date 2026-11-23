"""
items.py
--------
World objects that aren't the player or an enemy: the Pixel Core
progression currency, scavenged coins, a lore book collectible, chests
(including locked ones that cost coins to open), weapon pickups, and the
Projectile class used by ranged attacks (both the Witch's spell and the
player's bow).
"""

import math
import pygame
from src.settings import COLOR_GOLD
from src import assets
from src.data import ITEM_ICONS, WEAPONS


class PixelCore:
    """The ancient energy shard. Collecting these drives the evolution system."""

    SIZE = 14

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.collected = False
        self._t = 0.0

    def update(self, dt):
        self._t += dt

    def draw(self, surface, camera):
        if self.collected:
            return
        bob = int(math.sin(self._t * 4) * 4)
        pos = camera.apply(self.rect)
        pos.y += bob
        pygame.draw.rect(surface, COLOR_GOLD, pos, border_radius=3)
        pygame.draw.rect(surface, (255, 240, 180), pos, width=2, border_radius=3)


class Coin:
    """A stack of scavenged coins. Adds to the player's coin purse."""

    SIZE = 22

    def __init__(self, x, y, amount=None):
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.amount = amount if amount is not None else 5
        self.collected = False
        self.image = assets.load_image(ITEM_ICONS["coin"], (self.SIZE, self.SIZE), COLOR_GOLD)

    def draw(self, surface, camera):
        if self.collected:
            return
        surface.blit(self.image, camera.apply(self.rect))


class LoreBook:
    """
    An ancient tome. A rare find - grants the player a small bonus (extra
    pixel core progress) when picked up, hinting at the world's lore.
    """

    SIZE = 24

    def __init__(self, x, y, bonus_cores=1):
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.bonus_cores = bonus_cores
        self.collected = False
        self.image = assets.load_image(ITEM_ICONS["lore_book"], (self.SIZE, self.SIZE), (100, 80, 60))

    def draw(self, surface, camera):
        if self.collected:
            return
        surface.blit(self.image, camera.apply(self.rect))


class WeaponPickup:
    """Touch it to instantly equip a new weapon found in the wasteland."""

    SIZE = 26

    def __init__(self, x, y, weapon_key):
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.weapon_key = weapon_key
        self.collected = False
        cfg = WEAPONS[weapon_key]
        self.image = assets.load_image(cfg["icon"], (self.SIZE, self.SIZE), cfg["color"])

    def draw(self, surface, camera):
        if self.collected:
            return
        surface.blit(self.image, camera.apply(self.rect))


class Chest:
    """A wasteland loot chest. Opening one heals the player a little."""

    WIDTH, HEIGHT = 34, 28

    def __init__(self, x, y, locked=False, heal_amount=25, coin_cost=15):
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.opened = False
        self.locked = locked
        self.heal_amount = heal_amount
        self.coin_cost = coin_cost
        self.lock_icon = assets.load_image(ITEM_ICONS["lock"], (18, 16), COLOR_GOLD)

    def try_open(self, player):
        """Returns True if the chest opened (or was already open)."""
        if self.opened:
            return True
        if self.locked:
            if player.coins < self.coin_cost:
                return False
            player.coins -= self.coin_cost
        self.opened = True
        player.heal(self.heal_amount)
        return True

    def draw(self, surface, camera):
        color = (110, 90, 60) if not self.opened else (70, 60, 45)
        pos = camera.apply(self.rect)
        pygame.draw.rect(surface, color, pos)
        pygame.draw.rect(surface, (40, 30, 20), pos, width=2)
        if self.locked and not self.opened:
            lock_pos = pos.copy()
            lock_pos.x += (pos.width - self.lock_icon.get_width()) // 2
            lock_pos.y -= 6
            surface.blit(self.lock_icon, lock_pos)


class Projectile:
    """Simple straight-line projectile used by the Witch and the player's bow."""

    def __init__(self, x, y, direction, speed, damage, color, owner="enemy"):
        self.rect = pygame.Rect(x, y, 10, 10)
        self.direction = 1 if direction >= 0 else -1
        self.speed = speed
        self.damage = damage
        self.color = color
        self.owner = owner  # "enemy" or "player" - decides what it can hit
        self.alive = True
        self.lifetime_ms = 3000

    def update(self, dt_ms):
        self.rect.x += int(self.speed * self.direction)
        self.lifetime_ms -= dt_ms
        if self.lifetime_ms <= 0:
            self.alive = False

    def draw(self, surface, camera):
        pos = camera.apply(self.rect)
        pygame.draw.ellipse(surface, self.color, pos)
