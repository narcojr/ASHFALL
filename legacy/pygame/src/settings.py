"""
settings.py
-----------
All the "knobs" for the game live here. Change numbers in this file to
change how the game feels without touching any game logic elsewhere.
"""

# ---------------------------------------------------------------- WINDOW
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60
GAME_TITLE = "ASHFALL - Rise From The Ashes"

# ---------------------------------------------------------------- COLORS
COLOR_BG_TOP = (20, 14, 30)
COLOR_BG_BOTTOM = (60, 45, 70)
COLOR_GROUND = (70, 60, 65)
COLOR_PLATFORM = (95, 80, 85)
COLOR_WHITE = (240, 240, 240)
COLOR_BLACK = (10, 10, 10)
COLOR_RED = (200, 40, 40)
COLOR_GOLD = (230, 180, 60)
COLOR_BLUE = (70, 140, 220)
COLOR_PURPLE = (120, 60, 160)
COLOR_UI_BG = (20, 20, 25, 180)

# ---------------------------------------------------------------- PHYSICS
GRAVITY = 0.6
MAX_FALL_SPEED = 14
GROUND_FRICTION = 0.85

# ---------------------------------------------------------------- WORLD
TILE_SIZE = 32
LEVEL_WIDTH_TILES = 60          # how wide the scrolling level is
GROUND_Y = SCREEN_HEIGHT - 80   # top of the ground strip

# ---------------------------------------------------------------- PLAYER
PLAYER_START_X = 100
PLAYER_START_Y = GROUND_Y - 64
PLAYER_MOVE_SPEED = 4.2
PLAYER_JUMP_POWER = -11.5
PLAYER_ATTACK_COOLDOWN = 350    # ms
PLAYER_HURT_COOLDOWN = 700      # ms of invulnerability after being hit
PLAYER_STAMINA_REGEN = 0.15
ATTACK_STAMINA_COST = 12

# ---------------------------------------------------------------- CONTROLS
# Change these if you want different keybinds. See pygame.key constants.
import pygame

KEY_LEFT = (pygame.K_a, pygame.K_LEFT)
KEY_RIGHT = (pygame.K_d, pygame.K_RIGHT)
KEY_JUMP = (pygame.K_SPACE, pygame.K_w, pygame.K_UP)
KEY_ATTACK = (pygame.K_j, pygame.K_RETURN)
KEY_PAUSE = (pygame.K_ESCAPE,)
KEY_INTERACT = (pygame.K_e,)
