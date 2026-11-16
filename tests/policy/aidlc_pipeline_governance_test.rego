package pipeline

ok_pipe := {"pipeline": {"name": "p", "tags": {"aidlc": "inception"}, "stages": [
	{"stage": {"spec": {"execution": {"steps": [{"step": {"type": "Run", "name": "k", "spec": {"envVariables": {"ANTHROPIC_API_KEY": "<+secrets.getValue(\"anthropic_api_key\")>"}}}}]}}}},
	{"stage": {"spec": {"execution": {"steps": [{"step": {"type": "HarnessApproval", "name": "a", "spec": {"approvers": {"disallowPipelineExecutor": true}}}}]}}}},
]}}

test_ok_pipeline_passes {
	count(deny) == 0 with input as ok_pipe
}

test_missing_approval_denied {
	p := {"pipeline": {"name": "p", "tags": {"aidlc": "x"}, "stages": []}}
	count(deny) > 0 with input as p
}

test_inline_api_key_denied {
	p := {"pipeline": {"name": "p", "tags": {"aidlc": "x"}, "stages": [
		{"stage": {"spec": {"execution": {"steps": [{"step": {"type": "Run", "name": "k", "spec": {"envVariables": {"ANTHROPIC_API_KEY": "sk-ant-inline"}}}}]}}}},
		{"stage": {"spec": {"execution": {"steps": [{"step": {"type": "HarnessApproval", "name": "a", "spec": {"approvers": {"disallowPipelineExecutor": true}}}}]}}}},
	]}}
	count(deny) > 0 with input as p
}

test_skip_permissions_denied {
	p := {"pipeline": {"name": "p", "tags": {"aidlc": "x"}, "stages": [
		{"stage": {"spec": {"execution": {"steps": [{"step": {"type": "Run", "name": "k", "spec": {"envVariables": {"CLAUDE_TRUST_FLAGS": "--dangerously-skip-permissions"}}}}]}}}},
		{"stage": {"spec": {"execution": {"steps": [{"step": {"type": "HarnessApproval", "name": "a", "spec": {"approvers": {"disallowPipelineExecutor": true}}}}]}}}},
	]}}
	count(deny) > 0 with input as p
}
