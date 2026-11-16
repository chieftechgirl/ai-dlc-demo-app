# AI-DLC Demo App

A tiny, dependency-free demo app that re-skins itself by **industry** and **company**, Harness-themed by default. Built for the AI-DLC project.

## Run

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

## Customize

| What | How |
|------|-----|
| Industry | Use the picker in the header, set `industry` in `config.json`, or add `?industry=insurance` to the URL |
| Company branding from a website | `python3 scripts/brand.py https://www.example.com --industry insurance` |
| Colors / name by hand | Edit `config.json` (or `?company=Acme&primary=%23ff6600` for a quick demo) |
| Add or edit industries | Edit `industries.json` (labels, statuses, KPIs, sample records) |

Industry keys: `retail`, `healthcare`, `financial-services`, `insurance`, `manufacturing`, `travel`, `technology`.

The website fetch is best effort: it reads the page title, Open Graph tags, icon link and `theme-color`. Check `config.json` afterwards and fix anything it got wrong.

## Reset to Harness

Set `config.json` back to the defaults (`company.name` "Harness", `https://www.harness.io`, primary `#0278D5`).
