import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import server  # noqa: E402
from src import art, campaign, data  # noqa: E402


class GameDataTests(unittest.TestCase):
    def test_levels_are_valid(self):
        for number in (1, 2, 3):
            self.assertEqual(campaign.validate(campaign.build_level(number)), [], "level %d" % number)

    def test_levels_are_repeatable(self):
        self.assertEqual(campaign.build_level(2), campaign.build_level(2))

    def test_level_contents(self):
        one, two, three = (campaign.build_level(n) for n in (1, 2, 3))
        self.assertEqual({e[2] for e in one["enemies"]}, {"low_level_knight"})
        self.assertTrue(two["spikes"] and two["icicles"] and two["fires"])
        self.assertIsNotNone(three["boss"])
        self.assertIsNone(three["end_x"])

    def test_art_tier_grows_with_level(self):
        self.assertEqual([campaign.build_level(n)["tier"] for n in (1, 2, 3)], [1, 2, 3])

    def test_hero_gets_stronger_without_growing(self):
        stages = data.EVOLUTION_STAGES
        for key in ("max_health", "max_stamina", "damage_mult", "speed_mult", "cores_required"):
            values = [s[key] for s in stages]
            self.assertEqual(values, sorted(values), key)
            self.assertEqual(len(set(values)), len(values), key)
        self.assertNotIn("size", stages[0])            # the body size is one constant for every stage
        self.assertEqual(len(data.HERO_SIZE), 2)

    def test_no_ranged_weapon_for_the_hero(self):
        self.assertEqual(len(data.WEAPONS), 7)
        self.assertNotIn("arcus_scavenger", data.WEAPONS)
        for weapon in data.WEAPONS.values():
            self.assertNotIn("ranged", weapon)
        for key in campaign.LEVEL_WEAPON.values():
            self.assertIn(key, data.WEAPONS)

    def test_art_files_exist(self):
        self.assertEqual(art.problems(), [])


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        server.SAVE_FILE = os.path.join(cls.tmp.name, "save.json")
        cls.httpd = server.make_server("127.0.0.1", 18000)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.tmp.cleanup()

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as r:
            return json.load(r)

    def post(self, path, body):
        req = urllib.request.Request(self.base + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            return json.load(r)

    def status(self, path, body=None):
        try:
            req = urllib.request.Request(self.base + path, body, {"Content-Type": "application/json"} if body else {})
            return urllib.request.urlopen(req).status
        except urllib.error.HTTPError as err:
            return err.code

    def test_config(self):
        cfg = self.get("/api/config")
        self.assertEqual(len(cfg["levels"]), 3)
        self.assertIn("dash_ms", cfg["physics"])
        self.assertEqual(cfg["hero_size"], list(data.HERO_SIZE))
        self.assertEqual(set(cfg["art"]["tiers"]), {"1", "2", "3"})
        self.assertEqual(cfg["art"]["tiers"]["1"]["pixel"], 3)   # level 1 is the chunkiest pixel art

    def test_levels(self):
        self.assertEqual(self.get("/api/level/3")["id"], 3)
        self.assertEqual(self.status("/api/level/9"), 404)
        self.assertEqual(self.status("/api/level/abc"), 404)

    def test_static_files(self):
        self.assertEqual(self.status("/"), 200)
        self.assertEqual(self.status("/js/main.js"), 200)
        self.assertEqual(self.status("/assets/art/ashpixel.ttf"), 200)
        self.assertEqual(self.status("/../server.py"), 404)
        self.assertEqual(self.status("/%2e%2e/server.py"), 404)

    def test_progress_and_settings(self):
        self.post("/api/reset", {})
        self.assertEqual(self.get("/api/save")["unlocked"], 1)
        saved = self.post("/api/complete", {"level": 1, "time": 50.5, "cores": 4, "coins": 10})
        self.assertEqual(saved["unlocked"], 2)
        saved = self.post("/api/complete", {"level": 1, "time": 80, "cores": 1, "coins": 1})
        self.assertEqual(saved["best"]["1"]["time"], 50.5)       # a slower run does not replace the best
        self.assertEqual(self.status("/api/complete", json.dumps({"level": 7}).encode()), 400)
        saved = self.post("/api/settings", {"master": 999, "music_on": False, "difficulty": "nope", "other": 1})
        self.assertEqual(saved["settings"]["master"], 100)
        self.assertFalse(saved["settings"]["music_on"])
        self.assertEqual(saved["settings"]["difficulty"], "normal")
        self.assertNotIn("other", saved["settings"])
        self.assertEqual(self.status("/api/settings", b"not json"), 400)


if __name__ == "__main__":
    unittest.main()
