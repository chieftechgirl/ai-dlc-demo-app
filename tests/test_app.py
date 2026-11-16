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


class RenderPipelineTests(unittest.TestCase):
    def setUp(self):
        import setup_harness
        self.sh = setup_harness
        self.files = sorted((ROOT / ".harness").glob("*.yaml"))

    def test_templates_have_no_personal_ids(self):
        for f in self.files:
            t = f.read_text()
            self.assertIn("YOUR_ORG_ID", t, f.name)
            self.assertIn("YOUR_PROJECT_ID", t, f.name)
            for bad in ("sandbox", "aidlc_claude_reference", "EeRjnXTnS4GrLG5VNNJZUw"):
                self.assertNotIn(bad, t, f"{f.name} leaks {bad}")

    def test_ids_are_filled_in(self):
        for f in self.files:
            out = self.sh.render(f.read_text(), "myorg", "myproj")
            self.assertNotIn("YOUR_", out)
            self.assertIn("orgIdentifier: myorg", out)
            self.assertIn("projectIdentifier: myproj", out)

    def test_insights_step_removed_by_default_and_kept_on_request(self):
        for name in ("aidlc-demo-inception.yaml", "aidlc-demo-construction.yaml"):
            t = (ROOT / ".harness" / name).read_text()
            self.assertIn("Notify_AIDI", t)
            self.assertNotIn("Notify_AIDI", self.sh.render(t, "o", "p"))
            self.assertNotIn("aidi_base_url", self.sh.render(t, "o", "p"))
            self.assertIn("Notify_AIDI", self.sh.render(t, "o", "p", insights=True))

    def test_human_approval_survives_every_option(self):
        t = (ROOT / ".harness" / "aidlc-demo-inception.yaml").read_text()
        for kw in ({}, {"provider": "bedrock"}, {"insights": True}):
            out = self.sh.render(t, "o", "p", **kw)
            self.assertIn("HarnessApproval", out)
            self.assertIn("disallowPipelineExecutor: true", out)
            self.assertIn("aidlc_evidence_gate", out)

    def test_bedrock_swaps_credentials(self):
        t = (ROOT / ".harness" / "aidlc-demo-construction.yaml").read_text()
        out = self.sh.render(t, "o", "p", provider="bedrock", region="eu-west-1", model="m-1")
        self.assertNotIn("ANTHROPIC_API_KEY", out)
        self.assertIn('CLAUDE_CODE_USE_BEDROCK: "1"', out)
        self.assertIn('AWS_REGION: "eu-west-1"', out)
        self.assertIn('CLAUDE_MODEL: "m-1"', out)
        self.assertNotRegex(out, r"AWS_(ACCESS|SECRET)[A-Z_]*: (?!<\+secrets)")

    def test_custom_endpoint_uses_secret_backed_token(self):
        t = (ROOT / ".harness" / "aidlc-demo-construction.yaml").read_text()
        out = self.sh.render(t, "o", "p", provider="custom", base_url="https://gw.example.com", model="m1")
        self.assertNotIn("ANTHROPIC_API_KEY", out)
        self.assertIn('ANTHROPIC_BASE_URL: "https://gw.example.com"', out)
        self.assertIn('ANTHROPIC_AUTH_TOKEN: <+secrets.getValue("model_endpoint_key")>', out)
        self.assertIn('CLAUDE_MODEL: "m1"', out)
        self.assertIn("disallowPipelineExecutor: true", out)

    def test_default_provider_keeps_secret_backed_api_key(self):
        t = (ROOT / ".harness" / "aidlc-demo-inception.yaml").read_text()
        out = self.sh.render(t, "o", "p")
        self.assertIn('ANTHROPIC_API_KEY: <+secrets.getValue("anthropic_api_key")>', out)

    def test_balanced_structure_after_stripping(self):
        # no dangling "- step:" lines and indentation stays even
        t = (ROOT / ".harness" / "aidlc-demo-construction.yaml").read_text()
        out = self.sh.render(t, "o", "p")
        self.assertEqual(out.count("- step:"), t.count("- step:") - 1)
        for line in out.split("\n"):
            self.assertEqual((len(line) - len(line.lstrip())) % 2, 0, line)


class HarnessConnectTests(unittest.TestCase):
    """No network: only the safety checks and the dry run."""

    def test_only_harness_hosts_over_https_get_the_key(self):
        import harness_connect as hc
        self.assertEqual(hc.check_base_url("https://app.harness.io"), "https://app.harness.io")
        self.assertEqual(hc.check_base_url("https://app3.harness.io/x"), "https://app3.harness.io")
        for bad in ("http://app.harness.io", "https://evil.example.com", "https://harness.io.evil.com",
                    "https://notharness.io", "ftp://app.harness.io"):
            with self.assertRaises(SystemExit, msg=bad):
                hc.check_base_url(bad)

    def run_cli(self, args, env):
        import subprocess
        base = {"PATH": "/usr/bin:/bin"}
        base.update(env)
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "harness_connect.py")] + args,
                              env=base, capture_output=True, text=True)

    def test_requires_credentials_in_environment(self):
        r = self.run_cli(["--org", "o", "--project", "p", "check"], {})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("HARNESS_API_KEY", r.stderr)

    def test_apply_without_yes_is_a_dry_run_and_never_prints_the_key(self):
        r = self.run_cli(["--org", "o", "--project", "p", "apply"],
                         {"HARNESS_ACCOUNT_ID": "acct1", "HARNESS_API_KEY": "SECRET-TOKEN-123"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Dry run", r.stdout)
        self.assertIn("Nothing was sent", r.stdout)
        self.assertNotIn("SECRET-TOKEN-123", r.stdout + r.stderr)


class ModelGuardTests(unittest.TestCase):
    """run-aidlc-headless.sh must refuse to run with no model access and accept each supported way in.
    A stub 'claude' on PATH means nothing real is ever called."""

    def run_script(self, extra_env):
        import os, subprocess, tempfile
        with tempfile.TemporaryDirectory() as d:
            stub = Path(d) / "claude"
            stub.write_text("#!/bin/sh\ncat >/dev/null\necho STUB_CLAUDE_OK\n")
            stub.chmod(0o755)
            env = {"PATH": f"{d}:/usr/bin:/bin", "HOME": d}
            env.update(extra_env)
            return subprocess.run(["bash", str(ROOT / "scripts" / "run-aidlc-headless.sh"), "inception", "test intent"],
                                  cwd=d, env=env, capture_output=True, text=True)

    def test_refuses_without_model_access(self):
        r = self.run_script({})
        self.assertEqual(r.returncode, 2)
        self.assertIn("No model access configured", r.stderr)

    def test_accepts_each_supported_route(self):
        for env in ({"ANTHROPIC_API_KEY": "x"},
                    {"ANTHROPIC_AUTH_TOKEN": "x", "ANTHROPIC_BASE_URL": "https://gw.example.com"},
                    {"CLAUDE_CODE_USE_BEDROCK": "1"},
                    {"CLAUDE_CODE_USE_VERTEX": "1"}):
            r = self.run_script(env)
            self.assertEqual(r.returncode, 0, f"{env}: {r.stderr}")
            self.assertIn("STUB_CLAUDE_OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
