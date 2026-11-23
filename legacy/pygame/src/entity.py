"""
entity.py
---------
Base class for anything that lives in the world and can move, take damage,
and be drawn: the Player and every Enemy inherit from this.
"""

import pygame
from src.settings import GRAVITY, MAX_FALL_SPEED, TILE_SIZE, GROUND_Y


class Entity:
    def __init__(self, x, y, width, height, color, max_health):
        self.rect = pygame.Rect(x, y, width, height)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.facing_right = True
        self.on_ground = False

        self.color = color
        self.image = None  # subclasses may set a real sprite surface

        self.max_health = max_health
        self.health = max_health
        self.alive = True

    # ---------------------------------------------------------- damage
    def take_damage(self, amount):
        if not self.alive:
            return
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    @property
    def health_percent(self):
        if self.max_health <= 0:
            return 0
        return max(0.0, self.health / self.max_health)

    # ---------------------------------------------------------- physics
    def apply_gravity(self):
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

    def move_and_collide(self, platforms):
        """Simple AABB platformer collision: move on each axis separately."""
        # Horizontal
        self.rect.x += int(self.vel_x)
        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.vel_x > 0:
                    self.rect.right = plat.left
                elif self.vel_x < 0:
                    self.rect.left = plat.right

        # Vertical
        self.rect.y += int(self.vel_y)
        self.on_ground = False

        # Ground strip (acts like a giant platform)
        ground_rect = pygame.Rect(-100000, GROUND_Y, 200000, TILE_SIZE * 4)
        all_solids = list(platforms) + [ground_rect]

        for plat in all_solids:
            if self.rect.colliderect(plat):
                if self.vel_y > 0:
                    self.rect.bottom = plat.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = plat.bottom
                    self.vel_y = 0

    # ---------------------------------------------------------- drawing
    def draw(self, surface, camera):
        pos = camera.apply(self.rect)
        if self.image is not None:
            img = self.image if self.facing_right else pygame.transform.flip(self.image, True, False)
            surface.blit(img, pos)
        else:
            pygame.draw.rect(surface, self.color, pos)
