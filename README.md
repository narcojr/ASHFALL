# ASHFALL

A snow-ruin action platformer that runs in the browser: HTML, CSS and vanilla JavaScript on a
canvas, with every sound and sound effect synthesized in the Web Audio API. No build step, no
dependencies.

![ASHFALL](static/assets/art/logo.png)

## Play it

**Locally, with saving enabled:**

    python server.py

It opens http://127.0.0.1:8000. Use `--port 9000` to change the port and `--no-browser` to stop it
opening a tab.

**Locally, static only (no backend):**

    python -m http.server 8000 -d static

**Hosted:** the whole game lives in `static/`. Drop that folder on any static host (GitHub Pages,
Netlify, Cloudflare Pages, itch.io) and it works; progress is stored in `localStorage` and the
level data is prebuilt JSON. The included GitHub Actions workflow
(`.github/workflows/pages.yml`) publishes `static/` to GitHub Pages on every push.

When the Python backend is present the game detects it automatically and saves through the API
instead of `localStorage`.

## Controls

| Key | Action |
|---|---|
| A / D or arrows | move |
| Space / W / Up | jump (let go early for a short hop) |
| J / K / Enter | attack (press again to chain a 3-hit combo) |
| Shift / L | dash (short burst, you cannot be hit while dashing) |
| E | open a chest (locked chests cost 15 coins) |
| Esc / P | pause |

On touch screens an on-screen pad and action buttons appear instead.

## The levels

1. **Frostbound Path** - only the basic enemy (Footman).
2. **Shattered Ruins** - more enemies plus traps: spikes, falling icicles and fire vents.
3. **The Dominion's Gate** - tougher enemies, then the boss fight.

## Art and power go up together

The hero, enemies, ground, props and backgrounds are all drawn from the same shapes and palette,
at three pixel sizes:

| Level | Art | One art pixel is | Hero when the level starts |
|---|---|---|---|
| 1 | chunky pixel art | 3 screen pixels | The Exile (HP 100, damage x1.0) |
| 2 | finer pixel art | 2 screen pixels | The Wanderer (HP 140, damage x1.3) |
| 3 | finest pixel art | 1 screen pixel | The Reclaimer (HP 190, damage x1.7) |

The hero is always the same size. Getting stronger (collecting Pixel Cores) raises health, stamina,
damage and speed and changes his cape and metal trim. The last form, The Heir Ascendant, needs 20 cores.

## Folders

    server.py            optional backend: serves the game, saves progress and settings
    src/                 game data (data.py, settings.py), levels (campaign.py), art list (art.py)
    static/              the game: index.html, css/, js/ and assets/art (all sprites, tiles, the font)
    static/api/          prebuilt JSON (config + level layouts) so the game runs with no server
    tools/art/           the scripts that draw every sprite (run build_art.py to redraw them)
    tools/build_web.py   regenerates static/api; --check fails if it is stale
    tests/               python -m unittest discover -s tests
    legacy/pygame/       the original desktop pygame version, kept for reference

Redraw the art after changing a drawing script:

    pip install numpy pillow scipy fonttools
    python tools/art/build_art.py
    python tools/build_web.py

## Backend API

The browser uses these when the server is running:

    GET  /api/config        stats, weapons, enemies, stages, traps, boss, art info
    GET  /api/level/<1-3>   a level layout (generated from a fixed seed and checked)
    GET  /api/save          progress and settings
    POST /api/settings      save settings
    POST /api/complete      finish a level (unlocks the next one, keeps best time)
    POST /api/death  /api/unlock_all  /api/reset
    GET  /api/health        used by the client to decide between API and static mode
