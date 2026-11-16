# Set this up in your own accounts

This demo has three layers. You can stop after layer 1 and still have something useful.

| Layer | What it is | You need |
|-------|------------|----------|
| 1. AI-DLC + a coding tool | AWS's [AI-DLC](https://github.com/awslabs/aidlc-workflows) running in Kiro, Cursor or Claude Code | A coding tool and the `aidlc` installer |
| 2. Model access | Where the model comes from | Your choice of endpoint: Anthropic API, your own AWS account with Amazon Bedrock, or any other model endpoint |
| 3. Harness | Pipelines that run AI-DLC in CI with enforced approvals, policy, tests, scan and deploy | Your own Harness account and a GitHub account |

Nothing here depends on anyone else's Harness project, org or secrets. Everything below uses placeholders you replace with your own values.

> **Status:** the pipelines were validated in one Harness account only. The Bedrock option and a fresh-account setup
> have not been run end to end. Treat this as a starting point and expect to adjust screens and names.
> AI-DLC and AI coding tools generate output that needs review, and model usage costs money. Use a test repo and a test account.

---

## Quick start: connect your own Harness tenant

This is the fastest way to test the Harness side in **your** account. It uses an API token from your tenant. Treat
the token like a password: it stays in your terminal environment and is never written into this repo.

1. **Find your account id.** It is the id in your Harness URL after `/account/`, for example `app.harness.io/ng/account/<ACCOUNT_ID>/...`.
2. **Pick or create an org and project.** In Harness, create a project (for example `ai_dlc_demo`). Note the **identifiers**, not the display names. The default org identifier is usually `default`.
3. **Create an API token.**
   - Quick test: your profile (bottom-left) > **My API Keys** > **API Key** > **Token**.
   - Shared or CI use: Account Settings > Access Control > **Service Accounts**, then add a token.
   - Give it permission to view the project and create pipelines in it (for example Project Admin on a throwaway project). Copy the token when it is shown; you cannot see it again.
4. **Put the token in your environment** (this stays in your shell session only):
```bash
export HARNESS_ACCOUNT_ID=<your account id>
export HARNESS_API_KEY=<your token>
```
5. **Check the connection** (read-only):
```bash
python3 scripts/harness_connect.py --org <org> --project <project> check
```
   You should see `OK: connected`. If not: `401` means the token is wrong or expired, `403` means it lacks permission, and `404` means the org, project or account id is wrong.
6. **Preview, then create the pipelines.** Add the model options from layer 2 if you are not using an Anthropic key.
```bash
python3 scripts/harness_connect.py --org <org> --project <project> apply          # dry run, sends nothing
python3 scripts/harness_connect.py --org <org> --project <project> apply --yes    # creates the 3 pipelines
```
   It never overwrites an existing pipeline. Other Harness clusters: add `--harness-url https://app3.harness.io`. The token is only ever sent to a `harness.io` host over https.
7. **Finish in the Harness UI** (the script does not create these): secrets, a GitHub connector, an approver group and the `aidlc_evidence_gate` policy set. Steps 3 to 6 of layer 3 below cover each one.
8. **Run `AIDLC Demo Self Test`** to prove the governance logic, then follow the live flow in [DEMO.md](../DEMO.md).
9. **When you are done testing,** revoke or delete the API token.

If you prefer not to use a token, skip this and paste the YAML by hand (layer 3, steps 7 and 8).

---

## Layer 1: AI-DLC with your coding tool (about 20 minutes)

Follow **[DEMO.md, Demo track B](../DEMO.md#demo-track-b-run-ai-dlc-interactively-in-kiro-or-cursor)**. It covers Kiro IDE, Kiro CLI, Cursor and Claude Code. You need no Harness account for this.

## Layer 2: Connect to the model endpoint of your choice

AI-DLC itself is provider-independent. Model access belongs to the coding tool that runs it (AWS calls the tool a "harness"). So there are two separate choices: **which tool runs AI-DLC**, and **where that tool gets its model**.

| Route | Use it when | Pipeline option | Harness secret(s) |
|-------|-------------|-----------------|-------------------|
| **A. Anthropic API** | You have an Anthropic API key | `--provider anthropic` (default) | `anthropic_api_key` |
| **B. Amazon Bedrock** | Models must stay in your AWS account | `--provider bedrock --aws-region <region>` | `aws_access_key_id`, `aws_secret_access_key` |
| **C. Any other endpoint** | You run a model gateway or proxy (an internal LLM gateway, LiteLLM, a cloud provider's compatible endpoint) | `--provider custom --base-url https://<your-endpoint>` | `model_endpoint_key` |
| **D. A different coding tool** | You prefer opencode, Codex CLI, GitHub Copilot, Cursor or Kiro | See "Use a different agent in CI" below | Whatever that tool needs |

For every route you can add `--model <model id or name>` to pass a model to the agent.

### Route A: Anthropic API key

Create a key in your Anthropic account and store it as the Harness secret `anthropic_api_key` (layer 3, step 3).

### Route B: Your own AWS account with Amazon Bedrock

1. In the AWS console, open **Amazon Bedrock > Model access** in your chosen region and enable the model you want.
2. Create an IAM identity that can invoke Bedrock models (permissions such as `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` for that model). Use the least access that works.
3. Create access keys and store them as the Harness secrets `aws_access_key_id` and `aws_secret_access_key`. Long-lived keys are fine for a throwaway demo account. For anything real, use short-lived credentials or OIDC instead.
4. Render with `--provider bedrock --aws-region <your-region>` (layer 3, step 7), optionally `--model <model id or inference profile>`.
5. AI-DLC also has its own Bedrock provider settings. See AWS's README (`aidlc config providers`) for anything beyond what the pipeline sets.

### Route C: Any other model endpoint

Point the agent at an endpoint you control or trust:

```bash
python3 scripts/setup_harness.py --org <org> --project <project> \
  --provider custom --base-url https://<your-endpoint> --model <model name>
```

Then create the Harness secret `model_endpoint_key` holding the token for that endpoint. The pipeline passes it to the agent as `ANTHROPIC_AUTH_TOKEN` and the URL as `ANTHROPIC_BASE_URL`.

Requirements and cautions:

- The default CI agent (Claude Code) speaks the **Anthropic Messages API** with tool use. Your endpoint must expose that API. If your model only offers a different API style, run a gateway that translates in front of it.
- Use `https://` only. Keep the token in a Harness secret, never in a file, a commit or a pipeline variable.
- Check what the endpoint's operator logs and retains. The agent sends your code and prompts to it.
- This route is untested with any particular gateway. Start with a trivial intent and confirm the Inception run produces records under `aidlc/`.

If no model route is configured, the AI-DLC step stops immediately with "No model access configured".

### Route D: Use a different agent in CI

The pipelines use Claude Code as the CI agent by default, but nothing downstream depends on it. The evidence check, policy, approvals, build, test, scan and deploy all read the `aidlc/` records, whichever tool wrote them. AWS's AI-DLC supports Kiro, Cursor, opencode, Codex CLI and GitHub Copilot, and each manages its own provider and model (see AWS's per-harness guides). For example, opencode takes its provider from your opencode config, which can point at many providers.

To switch the CI agent:

1. Copy `scripts/setup-claude.sh` to `scripts/setup-<agent>.sh`. Install that agent's CLI, then run `aidlc config --harness <name> --yes` and `aidlc doctor`.
2. Copy `scripts/run-aidlc-headless.sh`. Keep the prompt-building part, which tells the agent to run only one phase and never self-approve. Replace the final `claude -p ...` line with your agent's non-interactive command.
3. In `.harness/aidlc-demo-inception.yaml` and `aidlc-demo-construction.yaml`, point the Setup and Run steps at your scripts and supply that agent's credentials as Harness secrets instead of the model variables.
4. Run the Self Test, then Inception with a trivial intent.

Headless behavior differs by tool and release, and the renderer's `--provider` options only know the Claude Code routes above, so expect to test this route yourself.

On Kiro, model access comes with Kiro, so interactive use (layer 1) needs no provider setup.

---

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
| `anthropic_api_key` | Your Anthropic API key | Route A |
| `aws_access_key_id`, `aws_secret_access_key` | Your AWS credentials | Route B |
| `model_endpoint_key` | Token for your own model endpoint | Route C |
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

# Use any other model endpoint
python3 scripts/setup_harness.py --org <org> --project <project> --provider custom --base-url https://<your-endpoint>

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
| AI-DLC step fails immediately | No model access, or the wrong route. Check the secret for your route (`anthropic_api_key`, the AWS pair, or `model_endpoint_key`), the region or base URL, and that you rendered with the matching `--provider`. |
| Evidence check fails with 0 approvals | The check looks for the word "approved" in AI-DLC's audit files. If your tool records approvals differently, pass `--approval-pattern` to `scripts/aidlc-gate-check.py` in the pipeline. |
| `harness_connect.py check` returns 401 / 403 / 404 | 401: token wrong or expired. 403: token lacks permission on the project. 404: wrong `--org`, `--project` or `HARNESS_ACCOUNT_ID`. |
| Push to the repo is rejected | Check that `git_push_token` has write access to your fork. |
| Deploy succeeds but the site is empty | Enable Pages for the `gh-pages` branch (step 11). The first publish can take a minute or two. |

## What to customize next

- Swap the secret scan in Construction for a Harness STO step.
- Replace the Pages deploy with a Harness CD stage for your real target.
- Replace the local `flags.json` with Harness Feature Management.
- Change `industries.json` and `scripts/brand.py` to brand the demo for a customer (see the README).
