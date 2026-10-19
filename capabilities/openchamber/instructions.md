## Capability: OpenChamber

Use the `openchamber` tool for operator-requested session operations. Dispatch
with action `session.create` and parameters title, prompt, directory and
returnResult: true when the result must come back. Select an authorized available
model when creating; a send or fork normally reuses its existing model. Use
`session.send` for a new prompt to an exact sessionId; it starts work. Use
`session.messages` to read messages and `session.status` to inspect state only
when needed. End the turn while a returned result is pending; do not poll.

For an explicitly requested fresh-session handoff, checkpoint first, then create
a successor with the same directory, agent `{{LEAD_AGENT}}`, exact goal and a
prompt to read LEAD.md. Record the confirmed sessionId and notify a configured
agent owner via its live pointer. Tell workers dispatched through this integration
where to report using `session.send`; checkpoint workers on other channels and
give the operator their handover details. Record failed or uncertain deliveries. Do not claim all
workers moved automatically. Never enable goal mode without an explicit request.
Do not move sessions into worktrees or delete sessions as routine cleanup.
If the tool is unavailable, give the operator the saved handover and report the
blocked operation; ordinary local work remains available.
