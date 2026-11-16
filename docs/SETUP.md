# Set this up in your own accounts

This demo has three layers. You can stop after layer 1 and still have something useful.

| Layer | What it is | You need |
|-------|------------|----------|
| 1. AI-DLC + a coding tool | AWS's [AI-DLC](https://github.com/awslabs/aidlc-workflows) running in Kiro, Cursor or Claude Code | A coding tool and the `aidlc` installer |
| 2. Model access | Where the model comes from | An Anthropic API key **or** your own AWS account with Amazon Bedrock |
| 3. Harness | Pipelines that run AI-DLC in CI with enforced approvals, policy, tests, scan and deploy | Your own Harness account and a GitHub account |

Nothing here depends on anyone else's Harness project, org or secrets. Everything below uses placeholders you replace with your own values.

> **Status:** the pipelines were validated in one Harness account only. The Bedrock option and a fresh-account setup
> have not been run end to end. Treat this as a starting point and expect to adjust screens and names.
> AI-DLC and AI coding tools generate output that needs review, and model usage costs money. Use a test repo and a test account.

---

## Layer 1: AI-DLC with your coding tool (about 20 minutes)

Follow **[DEMO.md, Demo track B](../DEMO.md#demo-track-b-run-ai-dlc-interactively-in-kiro-or-cursor)**. It covers Kiro IDE, Kiro CLI, Cursor and Claude Code. You need no Harness account for this.

## Layer 2: Choose where the model comes from

Pick one. Both work with the pipelines in layer 3.

### Option A: Anthropic API key (simplest)

Create a key in your Anthropic account. You will store it as the Harness secret `anthropic_api_key` in layer 3.

### Option B: Your own AWS account with Amazon Bedrock

1. In the AWS console, open **Amazon Bedrock > Model access** in your chosen region and enable the Claude model you want.
2. Create an IAM identity that can invoke Bedrock models (permissions such as `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` for that model). Use the least access that works.
3. Create access keys for it, and store them as the Harness secrets `aws_access_key_id` and `aws_secret_access_key` in layer 3. Long-lived keys are fine for a throwaway demo account. For anything real, use short-lived credentials or OIDC instead.
4. When you render the pipelines (layer 3, step 7) pass `--provider bedrock --aws-region <your-region>`, and optionally `--model <model id or inference profile>`.
5. AI-DLC itself has Bedrock provider settings. See AWS's README (`aidlc config providers`) and your harness guide for anything beyond what the pipeline sets.

On the Kiro IDE and Kiro CLI, model access comes with Kiro, so layer 1 needs no provider setup.

## Layer 3: Your own Harness account

### 1. Prerequisites

- A Harness account with **CI** (Harness Cloud builds), **Approvals** and **Policy (Governance)** available. A free or trial account is a good place to start.
- A **GitHub** account where you can fork this repo and create a token.
- Your **org identifier** and **project identifier**. Create a project (for example `ai_dlc_demo`) in your own org. The default org identifier is usually `default`.

### 2. Fork the repo

On GitHub, click **Fork** on this repository. You will need `git push` rights to your fork, because the pipelines push review branches and the `gh-pages` site there.

### 3. Create secrets (in your Harness project)

Project Settings > Secrets > New Secret > Text. Enter values in the Harness UI. Never put them in a file or a commit.

| Secret identifier | What to put in it | Needed when |
|-------------------|-------------------|-------------|
| `git_push_token` | A GitHub token that can push to your fork (fine-grained: Contents read and write on that repo) | Always |
| `anthropic_api_key` | Your Anthropic API key | Option A |
| `aws_access_key_id`, `aws_secret_access_key` | Your AWS credentials | Option B |
| `aidi_api_key` | Harness API key for AI DLC Insights | Only with `--insights` |

### 4. Create a GitHub connector

Project Settings > Connectors > New Connector > GitHub. Point it at your fork's account, use HTTPS, and authenticate with a token stored as a Harness secret. You will select this connector when you run a pipeline.

### 5. Create an approver group

Project Settings > Access Control > User Groups > New. Add at least **one person other than yourself**. The pipelines block the person who started a run from approving it, so with a single user you cannot get past the first gate.

### 6. Create the policy

Governance > Policies > New Policy. Paste `harness/policies/aidlc_evidence_gate.rego`. Then create a **Policy Set** with the identifier **`aidlc_evidence_gate`** (the pipelines refer to it by that exact name), add the policy, set the entity type to **Custom**, event **On Run**, and enforce it. Create the policy set in the same project as your pipelines.

Optional: add `harness/policies/aidlc_pipeline_governance.rego` as a second policy set on **Pipeline / On Save**. It makes Harness reject any AI-DLC pipeline that lacks a human approval, an executor-cannot-approve rule or a secret-backed API key.

### 7. Render the pipelines for your account

The templates in `.harness/` use `YOUR_ORG_ID` and `YOUR_PROJECT_ID`. This fills them in:

```bash
python3 scripts/setup_harness.py --org <your_org_id> --project <your_project_id>
```

Common variations:

```bash
# Use Amazon Bedrock instead of an Anthropic API key
python3 scripts/setup_harness.py --org <org> --project <project> --provider bedrock --aws-region us-east-1

# Keep the optional AI DLC Insights event step
python3 scripts/setup_harness.py --org <org> --project <project> --insights
```

Output goes to `build/harness/` (not committed). The AI DLC Insights step is removed unless you pass `--insights`, because it needs an account variable most accounts do not have.

### 8. Import the pipelines

In Harness: Pipelines > Create a Pipeline > Inline, then open the **YAML** tab and paste each file from `build/harness/`:

1. `aidlc-demo-selftest.yaml` (no model key and no repo needed)
2. `aidlc-demo-inception.yaml`
3. `aidlc-demo-construction.yaml`

If the optional governance policy rejects a save, read its message. It names the rule that failed.

### 9. Prove the governance works (no model key needed)

Run **AIDLC Demo Self Test**. It runs OPA unit tests on the evidence-gate logic and checks it against your policy set. If it fails at the policy step, recheck step 6.

### 10. Run the demo

Follow the **Live flow** in [DEMO.md](../DEMO.md). When a pipeline asks for inputs, use your connector, your fork's name, the `main` branch and your approver group.

### 11. Turn on GitHub Pages

After the first successful Deploy, go to your fork's **Settings > Pages**, choose **Deploy from a branch**, branch `gh-pages`, folder `/ (root)`. The site is at `https://<your-github-user>.github.io/ai-dlc-demo-app/`. Add `?flag.overdueBadge=on` to turn the feature on.

---

## Troubleshooting

| Symptom | Likely cause and fix |
|---------|----------------------|
| `--org ... is not a valid Harness identifier` | Identifiers allow letters, digits, `_` and `$` and cannot start with a digit. Use the identifier, not the display name. |
| Policy step fails with "policy set not found" | The Policy Set must be named exactly `aidlc_evidence_gate` and live in the same project (or a parent scope) as the pipeline. |
| Stuck at the first approval | The person who ran the pipeline cannot approve it. Add a second user to the approver group. |
| `aidlc: command not found` in CI | The setup step installs AI-DLC and adds it to `PATH`. Check that step's log for the installer error. |
| Claude step fails immediately | No model access. Check the `anthropic_api_key` secret, or for Bedrock the AWS secrets, region and model access. |
| Evidence check fails with 0 approvals | The check looks for the word "approved" in AI-DLC's audit files. If your tool records approvals differently, pass `--approval-pattern` to `scripts/aidlc-gate-check.py` in the pipeline. |
| Push to the repo is rejected | Check that `git_push_token` has write access to your fork. |
| Deploy succeeds but the site is empty | Enable Pages for the `gh-pages` branch (step 11). The first publish can take a minute or two. |

## What to customize next

- Swap the secret scan in Construction for a Harness STO step.
- Replace the Pages deploy with a Harness CD stage for your real target.
- Replace the local `flags.json` with Harness Feature Management.
- Change `industries.json` and `scripts/brand.py` to brand the demo for a customer (see the README).
