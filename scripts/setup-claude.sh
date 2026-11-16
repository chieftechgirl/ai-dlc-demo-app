#!/usr/bin/env bash
# Install Claude Code + AI-DLC and configure the current project for Claude Code.
# Runs inside a Harness CI step (or locally). Idempotent.
#
# Env:
#   AIDLC_VERSION   optional release pin (see aidlc-workflows "Install and Lifecycle")
set -euo pipefail

if ! command -v claude >/dev/null 2>&1; then
  command -v npm >/dev/null 2>&1 || { echo "Claude Code CLI not found and npm is unavailable" >&2; exit 2; }
  echo "==> Installing Claude Code"
  npm install -g @anthropic-ai/claude-code
fi

if ! command -v aidlc >/dev/null 2>&1; then
  echo "==> Installing AI-DLC (awslabs/aidlc-workflows)"
  # The installer refuses root unless told otherwise; CI containers often run as root.
  ROOT_FLAG=""; [ "$(id -u)" = "0" ] && ROOT_FLAG="--allow-root"
  curl -fsSL https://github.com/awslabs/aidlc-workflows/releases/latest/download/install.sh | sh -s -- ${ROOT_FLAG}
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> Versions"
claude --version || true
aidlc version || true

echo "==> Configuring AI-DLC for Claude Code"
# Non-interactive form documented by aidlc-workflows ("Without questions").
aidlc config --harness claude --yes

aidlc doctor || echo "WARN: aidlc doctor reported warnings (advisory)"
