## Host: Claude Code

Run this lead as the main thread with `claude --agent {{LEAD_AGENT}}` to use
available Agent workers. When invoked as a subagent, respect the host's depth
limit; do the work yourself if further delegation is unavailable. Agent results
return through the calling conversation. Use `/{{CHECKPOINT_NAME}}` or load
the named skill before handover. Do not assume automatic continuation or
cross-session messaging from this agent definition.
