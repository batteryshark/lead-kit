## Capability: Pi goal tracking

Requires the operator-installed `pi-goal-x` package by tmonk (0.32.3).
Select this guidance independently of worker tools. An ordinary task or PROJECT.md
objective does not authorize persistent autonomous execution. Start or bind a goal
only when the operator explicitly requests goal mode for that objective. If the
tools are missing, report goal integration blocked and continue permitted local work.

Use `get_goal({})` to inspect the session's focused goal; retrieve omitted
requirements with `get_goal({section: "objective"})`. Verify the goal id, objective
and execution ownership before recording progress. Ask the operator to use
`/goal-focus` for an existing goal and `/goal-resume` to take execution ownership
when required. Never attach work to a different focused goal by inference.

The operator can use `/goal <idea>` to plan and confirm, or `/sisyphus <idea>` for
explicitly ordered work. On an explicit request to create a persistent goal,
`create_goal({objective: "<full approved objective>"})` creates and focuses it and
starts automatic continuation. Set `mode: "sisyphus"` or `token_budget` only when
requested. Preserve all acceptance criteria and ordered steps. Inspect the live
task-tool schema before using `set_goal_tasks` or `update_goal_task`.

Active goals continue automatically after successful executions by default.
`maxAutonomousRuns` unset means unlimited; zero disables automatic continuation.
Ask the operator to set an appropriate allowance in `/goal-settings` before an
autonomous run. Do not change settings, replenish allowance or resume on their
behalf without approval. `/goal-resume` renews the allowance period. That allowance
does not bound Pi's within-run tool loop or unrelated extension-triggered turns.

For a stop, decision or handover, checkpoint LEAD.md and use
`update_goal({status: "paused", reason: "<concrete reason>"})` for an owned active
goal; verify success and stop. `/goal-pause` is the operator control. The separate
`blocked` status requires a reason and the same blocker on three consecutive goal
turns; use immediate pause for a principal stop. New continuation waits require
the operator's `strictExecutionContract` opt-in. Follow the installed wait protocol
and returned wait identity; never create polling loops or enable strict mode yourself.

Call `update_goal({status: "complete"})` only after verifying every requirement.
When auditing is enabled, it requests independent completion review; rejection
leaves the goal open. Verify the returned completion state independently of your
claim or a worker result. Auditing is optional and doesn't require a worker pack.
Goals persist under the selected goal pool (default `.pi/goals`); focus is
session-local. Timers require Pi to stay open; another session needs explicit
resume for execution ownership. This pack provides no successor-session transport.
