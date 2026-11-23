"""Backend for ASHFALL: serves the game files and a small JSON API.

    python server.py            -> http://127.0.0.1:8000
    python server.py --port 9000 --no-browser
"""
import argparse
import json
import mimetypes
import os
import sys
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from src import art, campaign, data, settings  # noqa: E402

STATIC_DIR = os.path.join(ROOT, "static")
SAVE_FILE = os.path.join(ROOT, "save_data.json")
MAX_BODY = 64 * 1024
save_lock = threading.Lock()

DEFAULT_SETTINGS = {"master": 80, "music": 60, "sfx": 80, "music_on": True, "sfx_on": True,
                    "shake": True, "fps": False, "difficulty": "normal"}
SETTING_RULES = {
    "master": ("int", 0, 100), "music": ("int", 0, 100), "sfx": ("int", 0, 100),
    "music_on": ("bool",), "sfx_on": ("bool",), "shake": ("bool",), "fps": ("bool",),
    "difficulty": ("choice", tuple(campaign.DIFFICULTY)),
}


def new_save():
    return {"unlocked": 1, "best": {}, "deaths": 0, "settings": dict(DEFAULT_SETTINGS)}


def clean_settings(raw, current=None):
    out = dict(current or DEFAULT_SETTINGS)
    if not isinstance(raw, dict):
        return out
    for key, rule in SETTING_RULES.items():
        value = raw.get(key)
        if rule[0] == "int" and isinstance(value, int) and not isinstance(value, bool):
            out[key] = max(rule[1], min(rule[2], value))
        elif rule[0] == "bool" and isinstance(value, bool):
            out[key] = value
        elif rule[0] == "choice" and value in rule[1]:
            out[key] = value
    return out


def load_save():
    with save_lock:
        try:
            with open(SAVE_FILE, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, ValueError):
            return new_save()
    save = new_save()
    if not isinstance(raw, dict):
        return save
    level_ids = {str(level["id"]) for level in campaign.LEVELS}
    if isinstance(raw.get("unlocked"), int) and 1 <= raw["unlocked"] <= len(campaign.LEVELS):
        save["unlocked"] = raw["unlocked"]
    if isinstance(raw.get("best"), dict):
        save["best"] = {k: v for k, v in raw["best"].items() if k in level_ids and isinstance(v, dict)}
    if isinstance(raw.get("deaths"), int):
        save["deaths"] = max(0, raw["deaths"])
    save["settings"] = clean_settings(raw.get("settings"))
    return save


def write_save(save):
    with save_lock:
        fd, tmp = tempfile.mkstemp(dir=ROOT, prefix=".save_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(save, f, indent=2)
            os.replace(tmp, SAVE_FILE)
        except OSError:
            if os.path.exists(tmp):
                os.unlink(tmp)


def build_config():
    weapons = {name: dict(w) for name, w in data.WEAPONS.items()}
    return {
        "screen": {"w": settings.SCREEN_WIDTH, "h": settings.SCREEN_HEIGHT, "fps": settings.FPS},
        "physics": {
            "gravity": settings.GRAVITY, "max_fall": settings.MAX_FALL_SPEED, "ground_y": settings.GROUND_Y,
            "move_speed": settings.PLAYER_MOVE_SPEED, "jump_power": settings.PLAYER_JUMP_POWER,
            "attack_cooldown": settings.PLAYER_ATTACK_COOLDOWN, "hurt_cooldown": settings.PLAYER_HURT_COOLDOWN,
            "stamina_regen": settings.PLAYER_STAMINA_REGEN, "attack_stamina": settings.ATTACK_STAMINA_COST,
            "dash_speed": settings.PLAYER_DASH_SPEED, "dash_ms": settings.PLAYER_DASH_MS,
            "dash_cooldown": settings.PLAYER_DASH_COOLDOWN, "dash_stamina": settings.DASH_STAMINA_COST,
        },
        "hero_size": data.HERO_SIZE,
        "stages": data.EVOLUTION_STAGES,
        "weapons": weapons, "default_weapon": data.DEFAULT_WEAPON,
        "enemies": data.ENEMY_TYPES,
        "levels": campaign.LEVELS, "traps": campaign.TRAPS, "boss": campaign.BOSS,
        "difficulty": campaign.DIFFICULTY,
        "art": art.load(),
    }


config_cache = None
level_cache = {}


def get_config():
    global config_cache
    if config_cache is None:
        config_cache = build_config()
    return config_cache


def get_level(number):
    if number not in level_cache:
        level_cache[number] = campaign.build_level(number)
    return level_cache[number]


class Handler(BaseHTTPRequestHandler):
    server_version = "Ashfall/2.0"

    def log_message(self, fmt, *args):
        if os.environ.get("ASHFALL_VERBOSE"):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def read_body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if not 0 <= length <= MAX_BODY:
                return None
            return json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return None

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = urlparse(self.path).path
        if not path.startswith("/api/"):
            return self.send_static(path)
        if path == "/api/config":
            return self.send_json(get_config())
        if path == "/api/save":
            return self.send_json(load_save())
        if path == "/api/health":
            return self.send_json({"ok": True})
        if path.startswith("/api/level/"):
            tail = path[len("/api/level/"):]
            if tail.isdigit() and 1 <= int(tail) <= len(campaign.LEVELS):
                return self.send_json(get_level(int(tail)))
            return self.send_json({"error": "no such level"}, 404)
        self.send_json({"error": "unknown endpoint"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self.read_body()
        if not path.startswith("/api/"):
            return self.send_json({"error": "not found"}, 404)
        if not isinstance(body, dict):
            return self.send_json({"error": "invalid JSON body"}, 400)
        save = load_save()

        if path == "/api/settings":
            save["settings"] = clean_settings(body, save["settings"])
        elif path == "/api/complete":
            level = body.get("level")
            if not isinstance(level, int) or not 1 <= level <= len(campaign.LEVELS):
                return self.send_json({"error": "bad level"}, 400)
            result = {"time": round(self.number(body, "time", 36000), 1), "cores": int(self.number(body, "cores", 999)),
                      "coins": int(self.number(body, "coins", 99999))}
            best = save["best"].get(str(level))
            if not best or result["time"] < best.get("time", 1e9):
                save["best"][str(level)] = result
            save["unlocked"] = max(save["unlocked"], min(len(campaign.LEVELS), level + 1))
        elif path == "/api/death":
            save["deaths"] += 1
        elif path == "/api/unlock_all":
            save["unlocked"] = len(campaign.LEVELS)
        elif path == "/api/reset":
            fresh = new_save()
            fresh["settings"] = save["settings"]
            save = fresh
        else:
            return self.send_json({"error": "unknown endpoint"}, 404)
        write_save(save)
        self.send_json(save)

    @staticmethod
    def number(body, key, limit):
        value = body.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0
        return max(0, min(limit, value))

    def send_static(self, path):
        name = "index.html" if path in ("", "/") else path.lstrip("/")
        full = os.path.realpath(os.path.join(STATIC_DIR, name))
        root = os.path.realpath(STATIC_DIR)
        if not full.startswith(root + os.sep) or not os.path.isfile(full):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(b"404 not found")
            return
        kind = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if full.endswith(".ttf"):
            kind = "font/ttf"
        elif kind.startswith("text/") or kind in ("application/javascript", "application/json"):
            kind += "; charset=utf-8"
        with open(full, "rb") as f:
            payload = f.read()
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)


def make_server(host="127.0.0.1", port=8000, tries=20):
    for p in range(port, port + tries):
        try:
            return ThreadingHTTPServer((host, p), Handler)
        except OSError:
            continue
    raise SystemExit("No free port found")


def main():
    parser = argparse.ArgumentParser(description="ASHFALL backend")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    missing = art.problems()
    if missing:
        raise SystemExit("Missing art files, run tools/art/build_art.py first: " + ", ".join(missing[:5]))
    for number in range(1, len(campaign.LEVELS) + 1):
        get_level(number)

    httpd = make_server(args.host, args.port)
    url = "http://%s:%d/" % (args.host, httpd.server_address[1])
    print("ASHFALL is running at", url, "(Ctrl+C to stop)")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nBye!")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
