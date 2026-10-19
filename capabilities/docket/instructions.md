## Capability: Docket

Docket is a separate optional scheduler project: https://github.com/batteryshark/docket.
Only use an operator-configured installation and its supplied AGENT_USAGE.md/CLI,
HTTP API or MCP guide. If none is configured, report the missing integration;
never install or start a service implicitly.

A host with authorized API access can request a schedule. Delivery currently
targets OpenCode sessions through Docket's configured adapter. Rendering this
pack on Pi, Claude or Codex does not give those sessions wake support. Verify
the delivery target and adapter before promising a wake, and report an unsupported
target as blocked. For an approved OpenCode target, schedule the promised time or
recurring check using the installed guide; do not add a sleep/poll loop.
Scheduling does not authorize external contact or guarantee work completion.
