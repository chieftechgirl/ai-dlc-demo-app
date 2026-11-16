# AI-DLC Demo App

A tiny, dependency-free demo app that re-skins itself by **industry** and **company**, Harness-themed by default. Built for the AI-DLC project.

## How AI-DLC runs in Harness

The AI-DLC methodology is [AWS Labs' `aidlc-workflows`](https://github.com/awslabs/aidlc-workflows). Claude Code runs it unattended inside Harness CI. Harness adds the enforced approval gates, policy checks, build, test, scan, deploy and measurement around it.

```mermaid
flowchart TD
    I(["Client request (intent)"]) --> INC

    subgraph P1["Pipeline 1: AIDLC Demo Inception"]
        INC["Claude Code runs AI-DLC Inception<br/>requirements, design, plan"]:::aws
        EV1["Collect evidence from aidlc/ records<br/>state, audit trail, stage documents"]
        POL1{{"OPA policy: aidlc_evidence_gate"}}:::gov
        BR1[("Review branch<br/>aidlc/executionId")]
        G1{{"Human approval gate<br/>executor cannot self-approve"}}:::gov
        INC --> EV1 --> POL1 --> BR1 --> G1
    end

    G1 -->|approved| VER

    subgraph P2["Pipeline 2: AIDLC Demo Construction"]
        VER["Verify gate: refuse to build<br/>without approved evidence"]:::gov
        POL2{{"OPA policy re-check"}}:::gov
        CON["Claude Code runs AI-DLC Construction<br/>implementation and tests"]:::aws
        BT["Build and test<br/>python unittest"]
        SEC["Security scan<br/>gitleaks"]
        PUB[("Publish build to review branch")]
        G2{{"Release approval gate"}}:::gov
        DEP["Deploy to GitHub Pages<br/>gh-pages branch"]
        VER --> POL2 --> CON --> BT --> SEC --> PUB --> G2 --> DEP
    end

    DEP --> LIVE(["Live app, new feature dark<br/>behind a flag in flags.json"])
    LIVE --> FLAG{{"Turn the flag on live<br/>?flag.name=on"}}

    INC -.->|events| AIDI[/"AI DLC Insights"/]
    CON -.->|events| AIDI

    classDef aws fill:#FF9900,stroke:#B36B00,color:#000
    classDef gov fill:#0278D5,stroke:#014B8A,color:#fff
```

**Legend:** orange steps are AWS AI-DLC, run by Claude Code. Blue steps are Harness governance gates. Everything else is standard CI/CD.

| AI-DLC phase | Covered here | Notes |
|--------------|--------------|-------|
| Inception | Yes | Pipeline 1, stops at the first gate |
| Construction | Yes | Pipeline 2, runs only after approval |
| Operations | No | Not in these pipelines |

## Use your own AI coding tool (Kiro, Cursor, Claude Code)

AI-DLC is one core that runs natively in several tools. The Harness pipelines use Claude Code in CI; at your
desk you can use whichever you prefer. Install AI-DLC, then configure the project:

```bash
curl -fsSL https://github.com/awslabs/aidlc-workflows/releases/latest/download/install.sh | sh
aidlc config --harness kiro      # or: cursor, claude
aidlc doctor
```

Open the project in your tool and run `/aidlc <what you want to build>` (in Kiro IDE, choose **aidlc** in the agent picker first).
Full copy-paste steps, the Kiro CLI variants, and a hybrid flow that hands the result to Harness for gates and delivery
are in [DEMO.md](DEMO.md#demo-track-b-run-ai-dlc-interactively-in-kiro-or-cursor).

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
