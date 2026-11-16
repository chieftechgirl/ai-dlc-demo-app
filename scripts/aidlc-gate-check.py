#!/usr/bin/env python3
"""Collect AI-DLC evidence from the repo and evaluate it for Harness governance.

Reads AI-DLC records laid out as documented by awslabs/aidlc-workflows:

    aidlc/spaces/<space>/intents/<intent>/
        aidlc-state.md        where the work stands
        audit/                every question, answer and approval
        <phase>/<stage>/...   stage documents, reviews/review-NN.md

Writes an evidence JSON (--out) that the OPA policy in harness/policies/aidlc_gate.rego
evaluates through a Harness Policy step, and exits non-zero if --enforce is set and
minimum checks fail. Stdlib only.

The audit format is not parsed structurally: approvals are counted by keyword match
(--approval-pattern) because the exact event schema depends on the aidlc release.
Adjust the pattern after inspecting a real audit/ folder from your release.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def collect_intent(intent_dir: Path, approval_re: re.Pattern) -> dict:
    state = intent_dir / "aidlc-state.md"
    audit_dir = intent_dir / "audit"
    audit_files = sorted(p for p in audit_dir.rglob("*") if p.is_file()) if audit_dir.is_dir() else []

    approvals = 0
    audit_entries = 0
    for f in audit_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        audit_entries += max(1, text.count("\n## ")) if text.strip() else 0
        approvals += len(approval_re.findall(text))

    stage_docs = [p for p in intent_dir.rglob("*.md")
                  if "audit" not in p.relative_to(intent_dir).parts and p.name != "aidlc-state.md"]
    reviews = [p for p in stage_docs if p.parent.name == "reviews"]

    return {
        "intent": intent_dir.name,
        "path": str(intent_dir),
        "has_state_file": state.is_file(),
        "audit_files": len(audit_files),
        "audit_entries": audit_entries,
        "approval_events": approvals,
        "stage_documents": len(stage_docs) - len(reviews),
        "review_documents": len(reviews),
        "has_project_description": (intent_dir / "project-description.json").is_file(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="project root containing aidlc/")
    ap.add_argument("--intent", help="limit to one intent folder name (default: all)")
    ap.add_argument("--phase", default="inception", choices=["inception", "construction"])
    ap.add_argument("--min-approvals", type=int, default=1,
                    help="minimum approval events required (inception: >=1 once stage 1 approved)")
    ap.add_argument("--approval-pattern", default=r"(?i)\bapprove[ds]?\b",
                    help="regex counted as an approval event in audit files")
    ap.add_argument("--out", default="aidlc-evidence.json")
    ap.add_argument("--enforce", action="store_true", help="exit 1 if basic checks fail")
    args = ap.parse_args()

    root = Path(args.root)
    intents_glob = list(root.glob("aidlc/spaces/*/intents/*"))
    intents = [p for p in intents_glob if p.is_dir() and (not args.intent or p.name == args.intent)]
    approval_re = re.compile(args.approval_pattern)

    evidence = {
        "phase": args.phase,
        "min_approvals": args.min_approvals,
        "intents": [collect_intent(p, approval_re) for p in sorted(intents)],
    }

    failures = []
    if not evidence["intents"]:
        failures.append("no AI-DLC intent records found under aidlc/spaces/*/intents/")
    for it in evidence["intents"]:
        if not it["has_state_file"]:
            failures.append(f"{it['intent']}: missing aidlc-state.md")
        if it["audit_files"] == 0:
            failures.append(f"{it['intent']}: empty or missing audit trail")
        if it["approval_events"] < args.min_approvals:
            failures.append(f"{it['intent']}: {it['approval_events']} approval events < {args.min_approvals}")
    evidence["local_failures"] = failures

    Path(args.out).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    if failures:
        print("\nAI-DLC evidence check failures:", *failures, sep="\n  - ", file=sys.stderr)
        if args.enforce:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
