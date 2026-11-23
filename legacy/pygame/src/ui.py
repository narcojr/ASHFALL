"""
ui.py
-----
On-screen HUD: HP bar, Stamina bar, pixel core counter and current
evolution stage name - modeled after the "Gameplay Screen Design" mockup
(HP/STA bars top-left, moon icon, etc).
"""

import pygame
from src.settings import COLOR_RED, COLOR_BLUE, COLOR_GOLD, COLOR_WHITE, COLOR_BLACK, SCREEN_WIDTH
from src import assets
from src.data import WEAPONS


class HUD:
    def __init__(self):
        self.font = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.font_big = pygame.font.SysFont("consolas", 36, bold=True)

    def draw(self, surface, player, level_number=None, biome_name=None):
        self._draw_bar(surface, 20, 20, 200, 16, player.health_percent, COLOR_RED, "HP")
        self._draw_bar(surface, 20, 42, 200, 12, player.stamina / player.max_stamina, COLOR_BLUE, "STA")

        core_text = self.font.render(f"Pixel Cores: {player.pixel_core_count}", True, COLOR_GOLD)
        surface.blit(core_text, (20, 64))

        coin_text = self.font_small.render(f"Coins: {player.coins}", True, (230, 200, 120))
        surface.blit(coin_text, (20, 86))

        stage_text = self.font_small.render(
            f"{player.evolution.get_stage_name()}", True, COLOR_WHITE
        )
        surface.blit(stage_text, (20, 104))

        to_next = player.evolution.cores_to_next_stage()
        if to_next > 0:
            hint = self.font_small.render(f"Next evolution in {to_next} core(s)", True, (200, 200, 200))
            surface.blit(hint, (20, 122))

        self._draw_weapon(surface, player)

        if level_number is not None:
            self._draw_level_tag(surface, level_number, biome_name)

        if player.on_evolve_flash_ms > 0:
            self._draw_evolve_banner(surface, player)

    def _draw_weapon(self, surface, player):
        cfg = WEAPONS[player.weapon_key]
        icon = assets.load_image(cfg["icon"], (32, 32), cfg["color"])
        icon_pos = (SCREEN_WIDTH - 52, 20)
        pygame.draw.rect(surface, (20, 20, 25), (icon_pos[0] - 4, icon_pos[1] - 4, 40, 40))
        pygame.draw.rect(surface, COLOR_WHITE, (icon_pos[0] - 4, icon_pos[1] - 4, 40, 40), width=2)
        surface.blit(icon, icon_pos)
        name_text = self.font_small.render(cfg["display_name"], True, COLOR_WHITE)
        surface.blit(name_text, name_text.get_rect(topright=(SCREEN_WIDTH - 20, 62)))

    def _draw_level_tag(self, surface, level_number, biome_name):
        text = self.font.render(f"LEVEL {level_number}", True, COLOR_GOLD)
        surface.blit(text, text.get_rect(topright=(SCREEN_WIDTH - 20, 92)))
        if biome_name:
            sub = self.font_small.render(biome_name, True, (200, 200, 210))
            surface.blit(sub, sub.get_rect(topright=(SCREEN_WIDTH - 20, 114)))

    def _draw_bar(self, surface, x, y, w, h, percent, color, label):
        percent = max(0.0, min(1.0, percent))
        pygame.draw.rect(surface, (30, 30, 30), (x, y, w, h))
        pygame.draw.rect(surface, color, (x, y, int(w * percent), h))
        pygame.draw.rect(surface, COLOR_WHITE, (x, y, w, h), width=2)
        label_surf = self.font_small.render(label, True, COLOR_WHITE)
        surface.blit(label_surf, (x + w + 8, y - 2))

    def _draw_evolve_banner(self, surface, player):
        text = self.font_big.render(f"EVOLVED: {player.evolution.get_stage_name()}", True, COLOR_GOLD)
        rect = text.get_rect(center=(surface.get_width() // 2, 80))
        shadow = self.font_big.render(f"EVOLVED: {player.evolution.get_stage_name()}", True, COLOR_BLACK)
        surface.blit(shadow, (rect.x + 2, rect.y + 2))
        surface.blit(text, rect)
