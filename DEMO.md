# Demo script: AI-DLC, run and governed by Harness

Audience: engineering leaders and developers. About 15 minutes.
Story: a client request becomes a reviewed, tested, scanned, flag-guarded release on a live URL, with a human approving at each gate.

## One-time setup

Setup uses **your own** accounts: your Harness org and project, your GitHub fork, and your own model access
(an Anthropic API key, your own AWS account with Amazon Bedrock, or any other model endpoint). Nothing depends on anyone else's project.

Follow **[docs/SETUP.md](docs/SETUP.md)**. In short:

1. Fork this repo. Create the secrets, a GitHub connector, an approver group and the `aidlc_evidence_gate` policy set in your Harness project.
2. Fill in your org and project: `python3 scripts/setup_harness.py --org <your_org_id> --project <your_project_id>` (add `--provider bedrock` for your AWS account, or `--provider custom --base-url https://<endpoint>` for any other endpoint).
3. Paste the rendered YAML from `build/harness/` into Harness, then run **AIDLC Demo Self Test**. It needs no model key and proves the governance logic works.

Want to skip Harness for now? Run AI-DLC in Kiro, Cursor or Claude Code with **Demo track B** below.

## Live flow

| # | Step | What to say |
|---|------|-------------|
| 1 | Show the app at the default brand. Run `python3 scripts/brand.py https://www.<client>.com --industry <key>` and refresh. | "Same app, re-skinned to the client's industry and brand in seconds." |
| 2 | Run **Inception** with the intent below. | "The AI agent plans the work. It does not write code yet and it cannot approve itself." |
| 3 | Open the review branch `aidlc/<executionId>`: requirements, design, plan, audit trail. | "Every question, answer and decision is recorded as files in Git." |
| 4 | Show the **Evidence Policy** result, then **Approve** as a different user. | "Policy checks the evidence exists. A human, not the pipeline, opens the gate." |
| 5 | Run **Construction** with the Inception execution id (copy it from the Inception run). | "It refuses to start without approved evidence." |
| 6 | Watch Build and Test, Security Scan, and the branch publish. | "Tests and a secret scan run on AI-written code like any other code." |
| 7 | **Approve release**, then watch Deploy to GitHub Pages. | "A second human gate before anything ships." |
| 8 | Open the live URL. Toggle the flag: `?flag.overdueBadge=on`. | "Ships dark. Turn it on for the audience live, and off if anything looks wrong." |

## Sample intent

> Add an "Overdue" badge to any record that has stayed in its first status for more than 3 days. Show it only when the `overdueBadge` flag is on (see `flag()` in app.js and `flags.json`; default off). Add unit tests under tests/. Keep the app dependency-free.

Swap the wording for the client's industry (claims, cases, orders, work orders).

## Demo track B: run AI-DLC interactively in Kiro or Cursor

The Harness pipelines run AI-DLC unattended in CI with a coding agent (Claude Code in the reference pipelines, swappable). AI-DLC itself is one harness-neutral
core that also runs natively in **Kiro** (IDE and CLI) and **Cursor**, so a developer can do the same work
at their desk with the tool they already use. Same method, same `aidlc/` records in the repo.

| Tool | Configure (run in the project root) | Open | Start |
|------|-------------------------------------|------|-------|
| Kiro IDE (>= 1.1.70) | `aidlc config --harness kiro` | Open the project folder in Kiro, then choose **aidlc** in the chat panel's agent picker | `/aidlc <intent>` |
| Kiro CLI (>= 2.24.1) | `aidlc config --harness kiro` | `kiro-cli --v3` | `/aidlc <intent>` |
| Kiro CLI (V2, older) | `aidlc config --harness kiro-v2` | `kiro-cli --v2` | `/aidlc <intent>` |
| Cursor | `aidlc config --harness cursor` | Open the project in Cursor, or run `agent` | `/aidlc <intent>` |
| Claude Code | `aidlc config --harness claude` | `claude` | `/aidlc <intent>` |

Source of truth: [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) (see its harness guides for Kiro and Cursor).
Older AI-DLC releases (2.11.3 and earlier) named the Kiro harnesses the other way round (`kiro-ide`, and `kiro` for CLI V2). If
`--harness kiro` is rejected, check AWS's note in that README.

### Copy-paste steps (Kiro or Cursor)

1. **Install AI-DLC once** (macOS, Linux or WSL):
```bash
curl -fsSL https://github.com/awslabs/aidlc-workflows/releases/latest/download/install.sh | sh
```
2. **Get the demo app and configure your tool:**
```bash
git clone https://github.com/chieftechgirl/ai-dlc-demo-app.git
cd ai-dlc-demo-app
aidlc config --harness kiro      # or: cursor
aidlc doctor
```
3. **Open the project** in Kiro or Cursor as in the table. In Kiro IDE, pick **aidlc** in the agent picker first.
   If Kiro asks whether you trust the folder, choose **Trust** only for a project you own or have reviewed
   (trusting lets the folder's `.kiro` hooks run commands on your machine).
4. **Start the workflow** by pasting this into the chat:
```text
/aidlc Add an "Overdue" badge to any record that has stayed in its first status for more than 3 days. Show it only when the overdueBadge flag is on (see flag() in app.js and flags.json; default off). Add unit tests under tests/. Keep the app dependency-free.
```
5. **Answer AI-DLC's questions and approve each gate in the chat.** It stops at approval gates by design. Approve only after reading the stage output.
6. **Check the evidence it wrote:**
```bash
ls aidlc/spaces/*/intents/*
python3 scripts/aidlc-gate-check.py --phase inception --min-approvals 1 --out aidlc-evidence.json
```
7. **Run the tests and the app:**
```bash
python3 -m unittest discover -s tests -v
python3 -m http.server 8000
```
Open http://localhost:8000/?flag.overdueBadge=on and compare with the flag off.

### Hybrid: Kiro or Cursor locally, Harness for the gates and delivery (untested)

The Construction pipeline only needs an `aidlc/<id>` branch containing the approved records, so it does not care
which tool wrote them. After step 5, in your terminal:
```bash
git checkout -b aidlc/kiro-demo-1
git add aidlc
git commit -m "AI-DLC inception artifacts (Kiro)"
git push origin aidlc/kiro-demo-1
```
Then run **AIDLC Demo Construction** in Harness with `inception_execution_id` set to `kiro-demo-1`. It verifies the
evidence, applies policy, builds, tests, scans, waits for release approval, and deploys.

Two things to check on a dry run, because the gate reads files rather than a fixed schema:
- The evidence check counts approvals by matching the word "approve/approved" in the audit files. If Kiro or Cursor
  records approvals differently, pass `--approval-pattern` to `scripts/aidlc-gate-check.py` in the pipeline.
- The check expects records under `aidlc/spaces/*/intents/*`. Confirm that path after `aidlc doctor` and step 5.

### What to say about Kiro to the AWS solution architect

```
AI-DLC is one core that runs in Kiro, Cursor and Claude Code. In Kiro the developer drives it
interactively. In Harness the same method runs unattended in CI, with approvals the platform
enforces. Either way the records land in the same aidlc/ folder in Git, so Harness can check
the evidence and handle the build, scan, deploy and flag, whichever tool produced the work.
```

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
