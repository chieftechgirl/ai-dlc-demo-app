# Demo script: AI-DLC with Claude Code, run and governed by Harness

Audience: engineering leaders and developers. About 15 minutes.
Story: a client request becomes a reviewed, tested, scanned, flag-guarded release on a live URL, with a human approving at each gate.

## One-time setup (about 15 minutes)

1. **Fork or clone this repo** into your own GitHub account.
2. **Harness account**: you need CI, Approvals and Policy enabled.
3. **Secrets** (project scope): `anthropic_api_key` (Anthropic API key) and `git_push_token` (GitHub token that can push branches to your fork).
4. **Connector**: a GitHub connector with access to your fork.
5. **Policy set** `aidlc_evidence_gate`: create it from `harness/policies/aidlc_evidence_gate.rego` (entity: Custom, event: On Run). Optionally add `aidlc_pipeline_governance.rego` for Pipeline / On Save.
6. **User group** that will approve gates (the person running the pipeline cannot approve their own run).
7. **Pipelines**: create from the YAML in `.harness/` (Inception, Construction, Self Test). Set `projectIdentifier` and `orgIdentifier` to yours.
8. **GitHub Pages**: Settings > Pages > Deploy from branch `gh-pages` (created on first deploy).
9. **Optional**: `aidi_api_key` secret and `aidi_base_url` account variable send events to AI DLC Insights. Without them that step is a no-op.

Run **AIDLC Demo Self Test** first. It needs no API key and proves the governance logic works.

## Live flow

| # | Step | What to say |
|---|------|-------------|
| 1 | Show the app at the default brand. Run `python3 scripts/brand.py https://www.<client>.com --industry <key>` and refresh. | "Same app, re-skinned to the client's industry and brand in seconds." |
| 2 | Run **Inception** with the intent below. | "Claude plans the work. It does not write code yet and it cannot approve itself." |
| 3 | Open the review branch `aidlc/<executionId>`: requirements, design, plan, audit trail. | "Every question, answer and decision is recorded as files in Git." |
| 4 | Show the **Evidence Policy** result, then **Approve** as a different user. | "Policy checks the evidence exists. A human, not the pipeline, opens the gate." |
| 5 | Run **Construction** with the Inception execution id. | "It refuses to start without approved evidence." |
| 6 | Watch Build and Test, Security Scan, and the branch publish. | "Tests and a secret scan run on AI-written code like any other code." |
| 7 | **Approve release**, then watch Deploy to GitHub Pages. | "A second human gate before anything ships." |
| 8 | Open the live URL. Toggle the flag: `?flag.overdueBadge=on`. | "Ships dark. Turn it on for the audience live, and off if anything looks wrong." |

## Sample intent

> Add an "Overdue" badge to any record that has stayed in its first status for more than 3 days. Show it only when the `overdueBadge` flag is on (see `flag()` in app.js and `flags.json`; default off). Add unit tests under tests/. Keep the app dependency-free.

Swap the wording for the client's industry (claims, cases, orders, work orders).

## Talking points

- **Governance by default**: separate approval gates, executor cannot self-approve, API key only from a Harness secret, explicit tool allowlist for the agent.
- **Evidence, not trust**: the gate reads audit files, state files and approval events, then OPA decides.
- **Safe delivery**: build, test, scan, approval, deploy, then a flag for the final exposure decision.
- **Measured**: events flow to AI DLC Insights.

## Known limits

- Feature flags here are a local `flags.json` plus URL override, which keeps the demo download-and-run. For real flag management, swap `flag()` for a Harness Feature Management SDK call.
- The Security Scan step is a secret scan only.
- Deploy is GitHub Pages (static). For a real target, replace it with a Harness CD stage.
- The AI-DLC headless question/answer behaviour depends on the aidlc release; see the reference repo's `docs/open-items.md`.
