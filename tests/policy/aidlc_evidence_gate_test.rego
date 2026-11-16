package aidlc

good := {"phase": "construction", "min_approvals": 1, "intents": [{"intent": "a", "has_state_file": true, "audit_files": 1, "approval_events": 2, "stage_documents": 3}]}

test_good_passes {
	count(deny) == 0 with input as good
}

test_no_intents_denied {
	count(deny) > 0 with input as {"phase": "inception", "min_approvals": 0, "intents": []}
}

test_missing_approval_denied {
	bad := object.union(good, {"intents": [{"intent": "a", "has_state_file": true, "audit_files": 1, "approval_events": 0, "stage_documents": 3}]})
	count(deny) > 0 with input as bad
}
