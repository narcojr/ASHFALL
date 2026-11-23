"""Builds the static JSON the web build needs, so the game can run without Python.

    python tools/build_web.py            writes static/api/config.json and static/api/level/*.json
    python tools/build_web.py --check    only verifies the files are up to date
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import server  # noqa: E402
from src import art, campaign  # noqa: E402

API_DIR = os.path.join(ROOT, "static", "api")


def payloads():
    files = {"config.json": server.build_config()}
    for number in range(1, len(campaign.LEVELS) + 1):
        files[os.path.join("level", "%d.json" % number)] = campaign.build_level(number)
    return files


def serialize(obj):
    return json.dumps(obj, indent=1, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Build ASHFALL static data")
    parser.add_argument("--check", action="store_true", help="fail if the checked-in files are stale")
    args = parser.parse_args()

    missing = art.problems()
    if missing:
        raise SystemExit("missing art: " + ", ".join(missing[:8]))

    stale = []
    for name, obj in payloads().items():
        path = os.path.join(API_DIR, name)
        text = serialize(obj)
        if args.check:
            try:
                with open(path, encoding="utf-8") as f:
                    if f.read() != text:
                        stale.append(name)
            except OSError:
                stale.append(name)
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote", os.path.relpath(path, ROOT))

    if stale:
        raise SystemExit("static data is stale: " + ", ".join(stale) + " (run tools/build_web.py)")
    if args.check:
        print("static data is up to date")


if __name__ == "__main__":
    main()
