import json
import os

ART_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "assets", "art")

# Each level uses one art tier. Tier 1 is the chunkiest pixel art, tier 3 the finest.
# Everything on screen (hero, enemies, ground, props, backgrounds) uses the same tier.
LEVEL_TIER = {1: 1, 2: 2, 3: 3}


def load():
    with open(os.path.join(ART_DIR, "art.json")) as f:
        return json.load(f)


def problems():
    """Missing art files, as a list of strings."""
    meta = load()
    missing = []
    for tier in meta["tiers"]:
        names = [f"hero_t{tier}_s{s}" for s in range(4)]
        names += [f"foe_{n}_t{tier}" for n in ("footman", "royal", "elite", "witch", "boss")]
        names += [f"{n}_t{tier}" for n in ("ground", "stone", "cap", "fire", "fire_big", "coin", "core", "book", "chest", "weapons")]
        names += [f"bg_{n}_t{tier}" for n in ("clouds", "mist", "forest", "ruins")]
        names += [f"prop_{n}_t{tier}" for n in ("rock_big", "rock", "rock_small", "tree", "pillar", "tombstone", "sign", "fence", "ice_plant", "lantern")]
        for n in names:
            if not os.path.isfile(os.path.join(ART_DIR, n + ".png")):
                missing.append(n + ".png")
    return missing
