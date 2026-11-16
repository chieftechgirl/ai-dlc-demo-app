package aidlc

# Evaluated by a Harness Policy step (Policy Set entity type: Custom).
# Input is the JSON written by scripts/aidlc-gate-check.py (aidlc-evidence.json).
#
# Harness policies deny when `deny` is a non-empty set/string.

# At least one AI-DLC intent record must exist.
deny[msg] {
	count(input.intents) == 0
	msg := "no AI-DLC intent records found: the change was not produced through AI-DLC"
}

# Every intent needs a state file.
deny[msg] {
	it := input.intents[_]
	not it.has_state_file
	msg := sprintf("intent '%s' has no aidlc-state.md", [it.intent])
}

# Every intent needs an audit trail.
deny[msg] {
	it := input.intents[_]
	it.audit_files == 0
	msg := sprintf("intent '%s' has an empty audit trail", [it.intent])
}

# Approvals must meet the minimum for this phase (0 during inception, >=1 for construction).
deny[msg] {
	it := input.intents[_]
	it.approval_events < input.min_approvals
	msg := sprintf("intent '%s' has %d approval events, need at least %d", [it.intent, it.approval_events, input.min_approvals])
}

# Construction requires reviewed stage documents, not only the state file.
deny[msg] {
	input.phase == "construction"
	it := input.intents[_]
	it.stage_documents == 0
	msg := sprintf("intent '%s' has no stage documents to build from", [it.intent])
}
