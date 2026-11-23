"""
evolution.py
------------
Implements the "Pixel Evolution System" from the design doc:

    Ancient energy known as Pixels remains hidden throughout the world.
    Every Pixel Core collected strengthens the player.

This class owns the progression logic ONLY - it doesn't know how to draw
or move anything. It just tracks cores collected and tells the Player when
to change stage. Keeping this separate makes it easy to rebalance without
touching player movement/combat code.
"""

from src.data import EVOLUTION_STAGES
from src import assets


class PixelEvolutionSystem:
    def __init__(self, player):
        self.player = player
        self.total_cores = 0
        self.stage_index = 0
        self._apply_stage(0, initial=True)

    @property
    def current_stage(self):
        return EVOLUTION_STAGES[self.stage_index]

    @property
    def next_stage(self):
        if self.stage_index + 1 < len(EVOLUTION_STAGES):
            return EVOLUTION_STAGES[self.stage_index + 1]
        return None

    def cores_to_next_stage(self):
        nxt = self.next_stage
        if nxt is None:
            return 0
        return max(0, nxt["cores_required"] - self.total_cores)

    def collect_core(self):
        self.total_cores += 1
        self._check_for_evolution()

    def _check_for_evolution(self):
        # Walk forward through stages while we qualify - handles the case
        # of picking up several cores that jump more than one stage at once.
        while True:
            nxt = self.next_stage
            if nxt is not None and self.total_cores >= nxt["cores_required"]:
                self.stage_index += 1
                self._apply_stage(self.stage_index)
            else:
                break

    def _apply_stage(self, index, initial=False):
        stage = EVOLUTION_STAGES[index]
        p = self.player

        # Preserve health/stamina ratio across the max-value change so the
        # player doesn't get punished (or exploited) by evolving.
        health_ratio = 1.0 if initial else p.health_percent
        stamina_ratio = 1.0 if initial else (p.stamina / p.max_stamina if p.max_stamina else 1.0)

        p.max_health = stage["max_health"]
        p.max_stamina = stage["max_stamina"]
        p.health = int(p.max_health * health_ratio)
        p.stamina = p.max_stamina * stamina_ratio
        p.damage_mult = stage["damage_mult"]
        p.speed_mult = stage["speed_mult"]
        p.color = stage["color"]

        # Resize the sprite rect but keep the character's feet planted.
        old_bottom = p.rect.bottom
        old_centerx = p.rect.centerx
        w, h = stage["size"]
        p.rect.width = w
        p.rect.height = h
        p.rect.centerx = old_centerx
        p.rect.bottom = old_bottom
        p.image = assets.load_image(f"player_stage_{index}.png", (w, h), stage["color"])

        if not initial:
            p.on_evolve_flash_ms = 900  # UI can use this to show a "flash" effect

    def get_stage_name(self):
        return self.current_stage["name"]
