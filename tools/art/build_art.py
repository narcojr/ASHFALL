"""Draws every sprite and tile used by the game. Run from the project root:

    python tools/art/build_art.py

Output goes to static/assets/art (PNG sheets) and static/assets/art/art.json.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import foes
import hero
import ui_art
import world
from font import build_ttf
from pix import save_sheet

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'static', 'assets', 'art')
os.makedirs(OUT, exist_ok=True)

TIERS = {1: 3, 2: 2, 3: 1}      # level tier -> pixel size (game px per art pixel)

# name, frames, fps, loops
HERO_META = {a[0]: {'frames': a[1], 'fps': a[3], 'loop': a[4]} for a in hero.ANIMS}
FOE_META = {'idle': (4, 6, True), 'walk': (6, 10, True), 'attack': (5, 11, False), 'hurt': (2, 10, False), 'death': (6, 9, False)}


def one(img, name, p):
    from PIL import Image
    Image.fromarray(img, 'RGBA').save(os.path.join(OUT, name + '.png'), optimize=True)


def main():
    meta = {'tiers': {}, 'hero': {}, 'foes': {}}
    for tier, p in TIERS.items():
        meta['tiers'][str(tier)] = {'pixel': p}
        for stage in range(4):
            rows = hero.render(p, stage)
            save_sheet(rows, os.path.join(OUT, f'hero_t{tier}_s{stage}.png'))
        for name in ('footman', 'royal', 'elite', 'witch', 'boss'):
            save_sheet(foes.render(name, p), os.path.join(OUT, f'foe_{name}_t{tier}.png'))

        w = world
        save_sheet([[w.ground_tile(p)]], os.path.join(OUT, f'ground_t{tier}.png'))
        save_sheet([[w.stone_tile(p, k) for k in ('gray', 'brick', 'navy')]], os.path.join(OUT, f'stone_t{tier}.png'))
        save_sheet([[w.snow_cap(p)]], os.path.join(OUT, f'cap_t{tier}.png'))
        for name, img in {'rock_big': w.rock(p, 66, 54, 1), 'rock': w.rock(p, 48, 36, 2), 'rock_small': w.rock(p, 36, 24, 3), 'tree': w.tree(p),
                          'pillar': w.pillar(p), 'tombstone': w.tombstone(p), 'sign': w.sign(p), 'fence': w.fence(p), 'ice_plant': w.ice_plant(p)}.items():
            save_sheet([[img]], os.path.join(OUT, f'prop_{name}_t{tier}.png'))
        save_sheet([[w.lantern(p, i) for i in range(2)]], os.path.join(OUT, f'prop_lantern_t{tier}.png'))
        save_sheet([[w.campfire(p, i) for i in range(4)]], os.path.join(OUT, f'fire_t{tier}.png'))
        save_sheet([[w.campfire(p, i, True) for i in range(4)]], os.path.join(OUT, f'fire_big_t{tier}.png'))
        save_sheet([[w.coin(p)]], os.path.join(OUT, f'coin_t{tier}.png'))
        save_sheet([[w.core(p)]], os.path.join(OUT, f'core_t{tier}.png'))
        save_sheet([[w.book(p)]], os.path.join(OUT, f'book_t{tier}.png'))
        save_sheet([[w.chest(p, s) for s in ('closed', 'open', 'locked')]], os.path.join(OUT, f'chest_t{tier}.png'))
        save_sheet([[w.weapon(p, k) for k in ('sword', 'spear', 'dagger', 'halberd', 'falx', 'axe', 'double_axe')]], os.path.join(OUT, f'weapons_t{tier}.png'))
        for name, fn in (('clouds', w.clouds), ('mist', w.mist), ('forest', w.forest), ('ruins', w.ruins)):
            save_sheet([[fn(p)]], os.path.join(OUT, f'bg_{name}_t{tier}.png'))
        print('tier', tier, 'done')

    ui_art.save(ui_art.button('normal'), os.path.join(OUT, 'btn.png'))
    ui_art.save(ui_art.button('hover'), os.path.join(OUT, 'btn_hover.png'))
    ui_art.save(ui_art.pause_button(), os.path.join(OUT, 'btn_pause.png'))
    ui_art.save(ui_art.panel(), os.path.join(OUT, 'panel.png'))
    ui_art.save(ui_art.icons(), os.path.join(OUT, 'icons.png'))
    ui_art.save(ui_art.logo(), os.path.join(OUT, 'logo.png'))
    build_ttf(os.path.join(OUT, 'ashpixel.ttf'))

    meta['hero'] = HERO_META
    meta['hero_cell'] = hero.CELL
    meta['hero_origin'] = list(hero.ORIGIN)
    meta['foe_cell'] = foes.CELL
    meta['foe_origin'] = list(foes.ORIGIN)
    meta['boss_cell'] = foes.BOSS_CELL
    meta['boss_origin'] = list(foes.BOSS_ORIGIN)
    meta['foes'] = {k: {'frames': v[0], 'fps': v[1], 'loop': v[2]} for k, v in FOE_META.items()}
    with open(os.path.join(OUT, 'art.json'), 'w') as f:
        json.dump(meta, f, indent=1)


if __name__ == '__main__':
    main()
