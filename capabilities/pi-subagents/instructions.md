## Capability: Pi subagents

Requires the operator-installed `pi-subagents` package by nicobailon (0.79.1).
Selection supplies guidance only. Delegate only when the request or applicable
project instructions authorize it. If exposed, `subagents_enable({})` enables
`subagent` on the next model request without launching work. If neither tool is
available, report delegation blocked and continue permitted local work yourself.

Read `subagent({action: "guide", options: {topic: "tool-reference"}})` for the
installed interface, and use `subagent({action: "list"})` to discover agents.
For a bounded local scout, use `subagent({agent: "scout", task: "<brief with scope,
paths and required evidence>", async: false, options: {timeoutMs: 120000,
context: "fresh", share: false}})`. Keep one writer per shared file set. Set a
runtime deadline and a finite fanout before dispatch; default to one child.
Writer deadlines need time to finish and checkpoint; hard tool/usage budgets
cannot guarantee a safe mutation boundary. Foreground children do not inherit
ambient extensions. Web research agents need their separately configured child
web tools; do not assume parent tools are present.

Inspect the returned output, errors and artifacts before accepting the result.
An async receipt confirms launch only. Record its exact run id and inspect
`subagent({action: "status", id: "<run-id>"})`; use `action: "steer"` with `message`
for live guidance. Resume only an eligible retained child with `action: "resume"`,
the exact `id` and `message`; this creates a new child from persisted context and
may refuse. A stopped run is not resumable. Capture partial changes on failure;
do not switch execution protocols without approval. Keep sharing disabled.

For authorized workflows, consult the installed workflow guide. Current workflows
use awaited `runs.run` / `runs.all` inside a workflow script; legacy top-level
`chain`, `tasks` and `parallel` are not the default interface. Active concurrency,
depth and cumulative spawn limits are separate; the default run-tree spawn cap
is 64. This pack does not configure those limits or provide remote owner delivery.
