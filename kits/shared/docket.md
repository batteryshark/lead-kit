## Shared services: Docket

Docket is external and optional. Only use an operator-configured installation
and its supplied AGENT_USAGE.md/CLI or MCP guide. If none is configured, report
the missing capability; never install or start a service implicitly. Docket can
wake a session for a promised time or recurring check: do not add a sleep/poll
loop. Scheduling does not authorize external contact.
