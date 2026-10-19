## Host: Codex

Select the lead instructions with `codex --profile {{LEAD_AGENT}}`. Use available
native subagents for bounded work: `spawn_agent`, `send_input`, `resume_agent`,
`wait_agent` and `close_agent` only as exposed by the host. Use its bounded wait
mechanism when results are needed; do not replace it with shell polling. A
profile does not enable goal continuation or change the operator's goal settings.
Invoke `${{CHECKPOINT_NAME}}` or read the named checkpoint skill before handover.
