#!/usr/bin/env python3
"""Render the pipeline templates in .harness/ for YOUR Harness account.

The templates use YOUR_ORG_ID / YOUR_PROJECT_ID placeholders. This fills them in and,
optionally, switches the model provider to Amazon Bedrock or removes the optional
AI DLC Insights step. Output goes to build/harness/, ready to paste into Harness
(Pipelines > Create a Pipeline > YAML) or import via the API.

Usage:
    python3 scripts/setup_harness.py --org default --project my_project
    python3 scripts/setup_harness.py --org default --project my_project \\
        --provider bedrock --aws-region us-east-1 --model <bedrock-model-id>

Stdlib only. Nothing is sent anywhere; it only writes local files.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / ".harness"
ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]{0,127}$")  # Harness identifier rules
ANTHROPIC_LINE = re.compile(r'^(\s*)ANTHROPIC_API_KEY: <\+secrets\.getValue\("anthropic_api_key"\)>\s*$')


def strip_insights(text: str) -> str:
    """Remove the 'Notify AI DLC Insights' step (needs an account variable most accounts lack)."""
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        if lines[i].strip() == "identifier: Notify_AIDI":
            # walk back to the "- step:" line that opens this step and drop what we already kept
            while out and out[-1].strip() != "- step:":
                out.pop()
            indent = len(out[-1]) - len(out[-1].lstrip())
            out.pop()
            i += 1
            while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > indent):
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def use_bedrock(text: str, region: str, model: str = "") -> str:
    """Swap the Anthropic API key for Amazon Bedrock settings on the AI-DLC run steps."""
    out = []
    for line in text.split("\n"):
        m = ANTHROPIC_LINE.match(line)
        if not m:
            out.append(line)
            continue
        pad = m.group(1)
        out += [
            f'{pad}CLAUDE_CODE_USE_BEDROCK: "1"',
            f'{pad}AWS_REGION: "{region}"',
            f'{pad}AWS_ACCESS_KEY_ID: <+secrets.getValue("aws_access_key_id")>',
            f'{pad}AWS_SECRET_ACCESS_KEY: <+secrets.getValue("aws_secret_access_key")>',
        ]
        if model:
            out.append(f'{pad}CLAUDE_MODEL: "{model}"')
    return "\n".join(out)


def render(text, org, project, provider="anthropic", region="us-east-1", model="", insights=False):
    text = text.replace("YOUR_ORG_ID", org).replace("YOUR_PROJECT_ID", project)
    if provider == "bedrock":
        text = use_bedrock(text, region, model)
    if not insights:
        text = strip_insights(text)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--org", required=True, help="your Harness organization identifier (often 'default')")
    ap.add_argument("--project", required=True, help="your Harness project identifier")
    ap.add_argument("--provider", choices=["anthropic", "bedrock"], default="anthropic",
                    help="where Claude gets its model access (default: anthropic API key)")
    ap.add_argument("--aws-region", default="us-east-1", help="AWS region for Bedrock")
    ap.add_argument("--model", default="", help="optional model id passed to Claude Code (Bedrock model or inference profile)")
    ap.add_argument("--insights", action="store_true", help="keep the AI DLC Insights event step (needs account variable aidi_base_url)")
    ap.add_argument("--out", default=str(ROOT / "build" / "harness"))
    args = ap.parse_args()

    for label, val in (("--org", args.org), ("--project", args.project)):
        if not ID_RE.match(val):
            sys.exit(f"{label} {val!r} is not a valid Harness identifier (letters, digits, _ and $; must not start with a digit)")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for src in sorted(SRC.glob("*.yaml")):
        dest = out / src.name
        dest.write_text(render(src.read_text(), args.org, args.project, args.provider,
                               args.aws_region, args.model, args.insights))
        written.append(dest)

    print(f"Rendered {len(written)} pipelines for org={args.org} project={args.project} provider={args.provider}:")
    for w in written:
        print(f"  {w.relative_to(ROOT) if w.is_relative_to(ROOT) else w}")
    print("\nNext: in Harness, Pipelines > Create a Pipeline > Inline > YAML tab, paste each file, Save. See docs/SETUP.md.")


if __name__ == "__main__":
    main()
