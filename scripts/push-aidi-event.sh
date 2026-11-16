#!/usr/bin/env bash
# Send an AI-DLC lifecycle event to Harness AI DLC Insights (AIDI) via the
# Custom CI/CD webhook API. No-op if AIDI_BASE_URL is unset so pipelines work
# before AIDI is configured.
#
# Usage: push-aidi-event.sh <event> [key=value ...]
#   e.g. push-aidi-event.sh inception_complete intent=inventory-api approvals=3
#
# Env:
#   AIDI_BASE_URL  e.g. https://app.harness.io/gateway/sei/api  (confirm for your account)
#   AIDI_API_KEY   Harness SEI API key (Harness secret)
#   AIDI_ENDPOINT  path appended to base (default: /v1/custom-cicd/events)  <-- PLACEHOLDER
#
# IMPORTANT: Harness docs describe a Custom CI/CD API (/v1/custom-cicd, requires the
# SEI_ENABLE_CUSTOM_CICD feature flag, an integration_id and an instance GUID). The
# exact job-run payload schema must be taken from the docs for your account; this
# script posts a generic event envelope that you map to that schema. See
# docs/open-items.md.
set -euo pipefail

EVENT="${1:?event name required}"; shift || true

if [ -z "${AIDI_BASE_URL:-}" ]; then
  echo "AIDI_BASE_URL not set; skipping AIDI event '${EVENT}'"
  exit 0
fi
: "${AIDI_API_KEY:?AIDI_API_KEY required when AIDI_BASE_URL is set}"

ENDPOINT="${AIDI_ENDPOINT:-/v1/custom-cicd/events}"

fields=""
for kv in "$@"; do
  k="${kv%%=*}"; v="${kv#*=}"
  fields="${fields},\"${k}\":\"${v//\"/\\\"}\""
done

BODY=$(printf '{"event":"%s","source":"aidlc-claude","pipeline_execution_id":"%s","timestamp":"%s"%s}' \
  "${EVENT}" "${HARNESS_EXECUTION_ID:-local}" "$(date -u +%FT%TZ)" "${fields}")

curl -fsS -X POST "${AIDI_BASE_URL}${ENDPOINT}" \
  -H "Authorization: ApiKey ${AIDI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "${BODY}" && echo "AIDI event sent: ${EVENT}"
