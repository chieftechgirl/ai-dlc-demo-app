#!/usr/bin/env bash
# Run an AI-DLC phase headlessly with Claude Code.
#
# Usage: run-aidlc-headless.sh <inception|construction> "<intent description>"
#
# Env:
#   ANTHROPIC_API_KEY  required, unless CLAUDE_CODE_USE_BEDROCK=1 with AWS credentials
#   CLAUDE_MODEL       optional model id passed as --model (Bedrock: model id or inference profile)
#   CLAUDE_TRUST_FLAGS permission flags. Default is an explicit tool allowlist, which also works as root.
#                      Avoid --dangerously-skip-permissions.
#   AIDLC_PROFILE      workflow profile hint: classic|express|feature|mvp|poc (default: express)
#   AIDLC_ANSWERS_FILE optional markdown file of pre-supplied answers (default: intent/answers.md)
#
# NOTE: AI-DLC is designed around human approval gates. In CI the agent is told to
# STOP at the gate for the phase and never self-approve; the Harness approval stage
# is the gate of record. Verify the headless question/answer behavior of your
# aidlc release (see docs/open-items.md).
set -euo pipefail

PHASE="${1:?phase required: inception|construction}"
INTENT="${2:?intent description required}"
PROFILE="${AIDLC_PROFILE:-express}"
ANSWERS_FILE="${AIDLC_ANSWERS_FILE:-intent/answers.md}"
FLAGS="${CLAUDE_TRUST_FLAGS:---permission-mode acceptEdits --allowedTools Read,Write,Edit,Glob,Grep,Bash}"

[ -n "${ANTHROPIC_API_KEY:-}" ] || [ "${CLAUDE_CODE_USE_BEDROCK:-}" = "1" ] || {
  echo "Set ANTHROPIC_API_KEY (Harness secret) or CLAUDE_CODE_USE_BEDROCK=1 with AWS credentials" >&2; exit 2; }

if [ -f "${ANSWERS_FILE}" ]; then
  ANSWERS_HINT="Pre-supplied answers to stage questions are in ${ANSWERS_FILE}; use them instead of asking. If a needed answer is missing, record the question in the stage questions file and stop."
else
  ANSWERS_HINT="No pre-supplied answers exist. Where a decision is required, record it as a question in the stage questions file and stop at that stage."
fi

case "${PHASE}" in
  inception)
    SCOPE="Run ONLY the Inception phase (requirements, design, planning). Do not write application code." ;;
  construction)
    SCOPE="Run ONLY the Construction phase (implementation and tests) for the already-approved Inception artifacts under aidlc/. Do not modify approved Inception documents." ;;
  *)
    echo "unknown phase: ${PHASE}" >&2; exit 2 ;;
esac

PROMPT="/aidlc ${INTENT}

Execution context: unattended CI run in Harness. Use the '${PROFILE}' workflow profile.
${SCOPE}
${ANSWERS_HINT}
Rules: never approve a gate yourself; stop and report at the first approval gate for this phase; keep all records under aidlc/."

echo "==> claude headless run: phase=${PHASE} profile=${PROFILE}"
# Prompt goes in on stdin so a variadic flag such as --allowedTools can never swallow it.
# shellcheck disable=SC2086
printf '%s' "${PROMPT}" | claude -p ${FLAGS} ${CLAUDE_MODEL:+--model "${CLAUDE_MODEL}"} | tee "aidlc-${PHASE}-run.log"
exit "${PIPESTATUS[1]}"
