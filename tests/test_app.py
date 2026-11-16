"""Stdlib-only checks the pipeline's Build and Test step runs.

Run locally:  python3 -m unittest discover -s tests -v
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def load(name):
    return json.loads((ROOT / name).read_text())


class ConfigTests(unittest.TestCase):
    def test_config_has_required_fields(self):
        c = load("config.json")
        for k in ("name", "websiteUrl", "tagline", "logoUrl"):
            self.assertIn(k, c["company"])
        for k in ("primary", "accent", "dark"):
            self.assertRegex(c["brand"][k], HEX)

    def test_config_industry_exists(self):
        self.assertIn(load("config.json")["industry"], load("industries.json"))

    def test_flags_are_booleans(self):
        for k, v in load("flags.json").items():
            self.assertIsInstance(v, bool, k)


class IndustryTests(unittest.TestCase):
    def test_every_industry_is_complete(self):
        for key, ind in load("industries.json").items():
            for f in ("label", "tagline", "record", "records", "statuses", "kpis", "samples"):
                self.assertIn(f, ind, f"{key} missing {f}")
            self.assertGreaterEqual(len(ind["statuses"]), 2, key)
            self.assertEqual(len(ind["kpis"]), 3, key)
            self.assertTrue(ind["samples"], key)


class BrandParserTests(unittest.TestCase):
    def test_first_title_only(self):
        import brand
        m = brand.Meta()
        m.feed("<head><title>Acme | Home</title></head><svg><title>Chevron</title></svg>")
        self.assertEqual(m.title, "Acme | Home")

    def test_meta_and_icons(self):
        import brand
        m = brand.Meta()
        m.feed('<meta property="og:site_name" content="Acme"><link rel="icon" href="/i.png">')
        self.assertEqual(m.meta["og:site_name"], "Acme")
        self.assertEqual(m.icons, ["/i.png"])


class OverrideTests(unittest.TestCase):
    def test_overrides_win(self):
        import brand
        cfg = {"company": {"name": "Long Site Title: Home"}, "brand": {"primary": "#0278D5", "accent": "#00ADE4", "dark": "#0B1727"}}
        brand.apply_overrides(cfg, name="Acme", primary="#E60028")
        self.assertEqual(cfg["company"]["name"], "Acme")
        self.assertEqual(cfg["brand"]["primary"], "#E60028")
        self.assertEqual(cfg["brand"]["accent"], "#00ADE4")

    def test_bad_color_rejected(self):
        import brand
        with self.assertRaises(SystemExit):
            brand.apply_overrides({"company": {}, "brand": {}}, primary="red")


if __name__ == "__main__":
    unittest.main()
