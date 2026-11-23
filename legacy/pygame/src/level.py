"""
level.py
--------
Builds the playable world from a layout dict (either the hand-crafted
INTRO_LEVEL_LAYOUT or one produced by level_generator.generate()), and
owns the per-frame update loop for everything living in it: enemies,
pickups, chests, decorations, and projectiles (both the Witch's spells and
the player's bow).
"""

import pygame
from src.settings import GROUND_Y, SCREEN_HEIGHT, SCREEN_WIDTH
from src.enemy import Enemy
from src.items import PixelCore, Coin, LoreBook, WeaponPickup, Chest
from src.decorations import Decoration
from src.data import STONE_THEMES
from src import assets


class Level:
    def __init__(self, layout, player):
        self.player = player
        self.layout = layout

        self.platforms = [pygame.Rect(*p) for p in layout["platforms"]]
        self.pixel_cores = [PixelCore(x, y) for (x, y) in layout["pixel_cores"]]
        self.coins = [Coin(x, y) for (x, y) in layout.get("coins", [])]
        self.chests = [Chest(x, y, locked=locked) for (x, y, locked) in layout["chests"]]
        self.lore_books = [LoreBook(x, y) for (x, y) in layout.get("lore_books", [])]
        self.weapon_pickups = [WeaponPickup(x, y, wk) for (x, y, wk) in layout.get("weapon_pickups", [])]
        self.decorations = [Decoration(x, y, kind) for (x, y, kind) in layout.get("decorations", [])]

        scale = layout.get("enemy_scale", {"health": 1.0, "damage": 1.0, "speed": 1.0})
        self.enemies = [
            Enemy(x, y, etype, health_mult=scale["health"], damage_mult=scale["damage"], speed_mult=scale["speed"])
            for (x, y, etype) in layout["enemies"]
        ]
        self.projectiles = []

        theme = STONE_THEMES[layout.get("stone_theme", 0) % len(STONE_THEMES)]
        self.theme_name = theme["name"]
        self.ground_texture = assets.load_texture_tile(theme["ground"], 64)
        self.platform_texture = assets.load_texture_tile(theme["platform"], 48)

        self.width_px = layout["level_end_x"] + 200
        self.level_end_x = layout["level_end_x"]
        self.level_complete = False

    # ---------------------------------------------------------- update
    def update(self, dt_ms, interact_pressed):
        player = self.player

        for core in self.pixel_cores:
            core.update(dt_ms / 1000.0)
            if not core.collected and player.rect.colliderect(core.rect):
                core.collected = True
                player.collect_pixel_core()

        for coin in self.coins:
            if not coin.collected and player.rect.colliderect(coin.rect):
                coin.collected = True
                player.collect_coins(coin.amount)

        for book in self.lore_books:
            if not book.collected and player.rect.colliderect(book.rect):
                book.collected = True
                for _ in range(book.bonus_cores):
                    player.collect_pixel_core()

        for wp in self.weapon_pickups:
            if not wp.collected and player.rect.colliderect(wp.rect):
                wp.collected = True
                player.equip_weapon(wp.weapon_key)

        if interact_pressed:
            for chest in self.chests:
                if not chest.opened and player.rect.colliderect(chest.rect.inflate(24, 12)):
                    chest.try_open(player)

        for enemy in self.enemies:
            if enemy.alive:
                enemy.update(dt_ms, self.platforms, player)
                proj = enemy.take_pending_projectile()
                if proj is not None:
                    self.projectiles.append(proj)

        # Player melee attack vs enemies
        if player.attack_hitbox is not None:
            for enemy in self.enemies:
                if enemy.alive and enemy.rect.colliderect(player.attack_hitbox):
                    enemy.take_damage(player.current_weapon_damage())

        # Player ranged attack (bow) spawns a projectile too
        player_proj = player.take_pending_projectile()
        if player_proj is not None:
            self.projectiles.append(player_proj)

        # Projectiles vs targets
        for proj in self.projectiles:
            proj.update(dt_ms)
            if proj.owner == "enemy" and proj.rect.colliderect(player.rect):
                player.take_damage(proj.damage)
                proj.alive = False
            elif proj.owner == "player":
                for enemy in self.enemies:
                    if enemy.alive and proj.rect.colliderect(enemy.rect):
                        enemy.take_damage(proj.damage)
                        proj.alive = False
                        break
        self.projectiles = [p for p in self.projectiles if p.alive]

        if player.rect.centerx >= self.level_end_x:
            self.level_complete = True

    # ---------------------------------------------------------- drawing
    def draw_background(self, surface, camera):
        # The ground band always spans the full screen width; the texture
        # itself scrolls via scroll_x so it appears to move with the camera.
        ground_screen_rect = pygame.Rect(0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y)
        assets.draw_tiled(surface, ground_screen_rect, self.ground_texture, scroll_x=camera.offset_x)

        for plat in self.platforms:
            screen_rect = camera.apply(plat)
            if screen_rect.right < 0 or screen_rect.left > SCREEN_WIDTH:
                continue
            assets.draw_tiled(surface, screen_rect, self.platform_texture, scroll_x=camera.offset_x + plat.x)
            pygame.draw.rect(surface, (20, 18, 20), screen_rect, width=2)

    def draw_objects(self, surface, camera):
        for deco in self.decorations:
            deco.draw(surface, camera)
        for core in self.pixel_cores:
            core.draw(surface, camera)
        for coin in self.coins:
            coin.draw(surface, camera)
        for book in self.lore_books:
            book.draw(surface, camera)
        for wp in self.weapon_pickups:
            wp.draw(surface, camera)
        for chest in self.chests:
            chest.draw(surface, camera)
        for enemy in self.enemies:
            if enemy.alive:
                enemy.draw(surface, camera)
        for proj in self.projectiles:
            proj.draw(surface, camera)
