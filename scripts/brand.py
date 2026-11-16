#!/usr/bin/env python3
"""Pull basic branding from a company website into config.json.

Usage:
    python3 scripts/brand.py https://www.example.com [--industry insurance]

Grabs the site name, tagline, logo/icon and theme color from the page's
<title>, Open Graph tags and icon links. Review config.json afterwards:
automatic extraction is a best guess, so edit anything that looks off.
"""
import argparse, json, re, sys, urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

CONFIG = Path(__file__).resolve().parent.parent / "config.json"


class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta, self.icons, self.title, self._in_title = {}, [], "", False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title" and not self.title:
            # first <title> only: inline SVGs often carry their own <title>s
            self._in_title = True
        elif tag == "meta":
            k = a.get("property") or a.get("name")
            if k and a.get("content"):
                self.meta[k.lower()] = a["content"]
        elif tag == "link" and "icon" in (a.get("rel") or "").lower() and a.get("href"):
            self.icons.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def apply_overrides(cfg, name=None, primary=None, accent=None, dark=None):
    """Explicit flags win over whatever was scraped from the site."""
    if name:
        cfg["company"]["name"] = name
    for key, val in (("primary", primary), ("accent", accent), ("dark", dark)):
        if val:
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", val):
                sys.exit(f"--{key} must look like #E60028, got {val!r}")
            cfg["brand"][key] = val
    return cfg


def main():
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("--industry", help="industry key from industries.json")
    p.add_argument("--name", help="override the company name (site titles are often long)")
    p.add_argument("--primary", help="override primary color, e.g. #E60028")
    p.add_argument("--accent", help="override accent color")
    p.add_argument("--dark", help="override header/dark color")
    args = p.parse_args()

    url = args.url if args.url.startswith("http") else "https://" + args.url
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ai-dlc-demo-app brand fetch)"})
    try:
        html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
    except Exception as e:
        sys.exit(f"Could not fetch {url}: {e}")

    m = Meta()
    m.feed(html)

    name = m.meta.get("og:site_name") or re.split(r"\s[|\-:–]\s", m.title.strip())[0] or url
    tagline = m.meta.get("og:description") or m.meta.get("description") or ""
    logo = urljoin(url, m.icons[-1]) if m.icons else (urljoin(url, m.meta["og:image"]) if m.meta.get("og:image") else "")
    color = m.meta.get("theme-color", "")

    cfg = json.loads(CONFIG.read_text())
    # tagline is left alone on purpose: if set, it overrides the industry tagline.
    cfg["company"].update({"name": name, "websiteUrl": url, "logoUrl": logo})
    if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        cfg["brand"]["primary"] = color
    if args.industry:
        cfg["industry"] = args.industry
    apply_overrides(cfg, args.name, args.primary, args.accent, args.dark)
    name = cfg["company"]["name"]
    CONFIG.write_text(json.dumps(cfg, indent=2) + "\n")

    print(f"Updated {CONFIG.name}:")
    print(f"  name     : {name}")
    print(f"  (site description, not saved: {tagline[:60]})")
    print(f"  logo     : {logo or '(none found)'}")
    print(f"  primary  : {cfg['brand']['primary']}" + ("" if (color or args.primary) else "  (no theme-color on site; unchanged, pass --primary to set it)"))


if __name__ == "__main__":
    main()
