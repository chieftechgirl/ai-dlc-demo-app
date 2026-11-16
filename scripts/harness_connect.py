#!/usr/bin/env python3
"""Connect YOUR Harness tenant to this demo: check access, then create the pipelines there.

Your API key is read from the environment only (never a command-line argument, never written to disk):

    export HARNESS_ACCOUNT_ID=<your account id>      # the id in your Harness URL after /account/
    export HARNESS_API_KEY=<service account token or personal access token>

Usage:
    # 1. read-only check: can I reach my tenant and see my project?
    python3 scripts/harness_connect.py --org <org> --project <project> check

    # 2. preview what would be created (nothing is sent)
    python3 scripts/harness_connect.py --org <org> --project <project> apply

    # 3. create the three pipelines in your project
    python3 scripts/harness_connect.py --org <org> --project <project> apply --yes

`apply` accepts the same --provider/--aws-region/--model/--base-url/--insights options as
setup_harness.py. It never overwrites an existing pipeline. It does not create secrets,
connectors, policies or user groups: do those in the Harness UI (see docs/SETUP.md).

The key is only sent to a harness.io host over https. Use --harness-url for other clusters
(for example https://app3.harness.io). Stdlib only. Not yet tested against tenants other than
the author's: treat failures as information and read the message.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import setup_harness  # noqa: E402

SRC = setup_harness.SRC


def check_base_url(url: str) -> str:
    u = urllib.parse.urlparse(url)
    host = (u.hostname or "")
    if u.scheme != "https" or not (host == "harness.io" or host.endswith(".harness.io")):
        sys.exit("--harness-url must be an https URL on a harness.io host (your API key is sent there)")
    return f"https://{host}"


def api_url(base: str, path: str, **query) -> str:
    return f"{base}{path}?{urllib.parse.urlencode(query)}"


def call(url: str, key: str, method="GET", body: bytes = None, content_type: str = None):
    headers = {"x-api-key": key, "Accept": "application/json"}
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach {url.split('?')[0]}: {e.reason}")


def short_error(text: str) -> str:
    try:
        d = json.loads(text)
        return str(d.get("message") or d.get("responseMessages") or text)[:300]
    except ValueError:
        return text[:300]


def need_env():
    acct, key = os.environ.get("HARNESS_ACCOUNT_ID", ""), os.environ.get("HARNESS_API_KEY", "")
    if not acct or not key:
        sys.exit("Set HARNESS_ACCOUNT_ID and HARNESS_API_KEY in your environment first (see the top of this file).")
    return acct, key


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--org", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--harness-url", default="https://app.harness.io")
    ap.add_argument("action", choices=["check", "apply"])
    ap.add_argument("--yes", action="store_true", help="with apply: actually create the pipelines")
    ap.add_argument("--provider", choices=["anthropic", "bedrock", "custom"], default="anthropic")
    ap.add_argument("--aws-region", default="us-east-1")
    ap.add_argument("--model", default="")
    ap.add_argument("--base-url", default="", help="model endpoint (with --provider custom)")
    ap.add_argument("--insights", action="store_true")
    a = ap.parse_args()

    for label, val in (("--org", a.org), ("--project", a.project)):
        if not setup_harness.ID_RE.match(val):
            sys.exit(f"{label} {val!r} is not a valid Harness identifier")
    base = check_base_url(a.harness_url)
    acct, key = need_env()

    if a.action == "check":
        status, text = call(api_url(base, f"/ng/api/projects/{a.project}",
                                    accountIdentifier=acct, orgIdentifier=a.org), key)
        if status == 200:
            name = json.loads(text).get("data", {}).get("project", {}).get("name", a.project)
            print(f"OK: connected. Project '{name}' ({a.org}/{a.project}) is visible with this key.")
            print("Next: create secrets, a GitHub connector, an approver group and the policy set (docs/SETUP.md), then 'apply'.")
            return
        hint = {401: "key rejected: check HARNESS_API_KEY and that the token has not expired",
                403: "key valid but lacks permission on this project",
                404: "project not found: check --org, --project and HARNESS_ACCOUNT_ID"}.get(status, "unexpected response")
        sys.exit(f"FAILED ({status}): {hint}. Server said: {short_error(text)}")

    # apply
    if a.provider == "custom" and not a.base_url.startswith("https://"):
        sys.exit("--provider custom needs --base-url https://<your-endpoint>")
    files = sorted(SRC.glob("*.yaml"))
    rendered = {f.name: setup_harness.render(f.read_text(), a.org, a.project, a.provider,
                                             a.aws_region, a.model, a.insights, a.base_url) for f in files}
    if not a.yes:
        print(f"Dry run. Would create {len(rendered)} pipelines in {a.org}/{a.project} at {base}:")
        for n in rendered:
            print(f"  {n}")
        print("Nothing was sent. Re-run with --yes to create them (existing pipelines are never overwritten).")
        return
    for name, yaml_text in rendered.items():
        url = api_url(base, "/pipeline/api/pipelines/v2", accountIdentifier=acct,
                      orgIdentifier=a.org, projectIdentifier=a.project)
        status, text = call(url, key, "POST", yaml_text.encode("utf-8"), "application/yaml")
        if status in (200, 201):
            print(f"created  {name}")
        elif "already exists" in text.lower() or "duplicate" in text.lower():
            print(f"skipped  {name} (a pipeline with that identifier already exists; not overwritten)")
        else:
            print(f"FAILED   {name} ({status}): {short_error(text)}")
    print("\nStill to do in the Harness UI: secrets, GitHub connector, approver group, policy set 'aidlc_evidence_gate'. See docs/SETUP.md.")


if __name__ == "__main__":
    main()
