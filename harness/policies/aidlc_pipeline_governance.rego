package pipeline

# Policy Set: entity type Pipeline, event On Save (or On Run).
# Applies to pipelines tagged aidlc: any Claude Code-driven AI-DLC pipeline must contain
# a human approval stage, and an AI-DLC run step must not be the final stage.

is_aidlc {
	input.pipeline.tags.aidlc
}

# Stages that contain a HarnessApproval step.
approval_stages[i] {
	input.pipeline.stages[i].stage.spec.execution.steps[_].step.type == "HarnessApproval"
}

has_approval {
	approval_stages[_]
}

deny[msg] {
	is_aidlc
	not has_approval
	msg := sprintf("AI-DLC pipeline '%s' must include a HarnessApproval step (human gate)", [input.pipeline.name])
}

# Approvals in AI-DLC pipelines must exclude the pipeline executor from approving their own run.
deny[msg] {
	is_aidlc
	step := input.pipeline.stages[_].stage.spec.execution.steps[_].step
	step.type == "HarnessApproval"
	not step.spec.approvers.disallowPipelineExecutor
	msg := sprintf("approval step '%s' must set disallowPipelineExecutor: true", [step.name])
}

# The Anthropic API key must come from a Harness secret, never inline.
deny[msg] {
	is_aidlc
	step := input.pipeline.stages[_].stage.spec.execution.steps[_].step
	val := step.spec.envVariables.ANTHROPIC_API_KEY
	not startswith(val, "<+secrets.getValue(")
	msg := sprintf("step '%s' sets ANTHROPIC_API_KEY without a Harness secret", [step.name])
}

# Unattended agents must use an explicit tool allowlist, not blanket permission skipping.
deny[msg] {
	is_aidlc
	step := input.pipeline.stages[_].stage.spec.execution.steps[_].step
	flags := step.spec.envVariables.CLAUDE_TRUST_FLAGS
	contains(flags, "--dangerously-skip-permissions")
	msg := sprintf("step '%s' must not use --dangerously-skip-permissions; use --allowedTools", [step.name])
}
