# Pi setup and interfaces

Use Pi 1.0.0 with its default `~/.pi/agent` directory. The npm host package is
`@earendil-works/pi-coding-agent`; its Node.js minimum is 22.19.0. Configure the
host and model separately before using the installed resources. The kit never
probes your Pi installation, auth or settings.

Follow the [README Pi path](../README.md#pi-10) to preview and install with
`--preset pi`. For custom packs, copy [presets/pi.json](../presets/pi.json) to a
stable saved config path and use `--lead-config` for each mode. Uninstall an
existing preset first if the copy keeps its name. With empty `capabilities`, the lead uses
Pi's ordinary tools and does the work itself. `/<agent> <task>` expands the one
rendered prompt; `/skill:<agent>-checkpoint [fresh]` loads the checkpoint skill.
The prompt has `description` and `argument-hint` metadata and appends `$ARGUMENTS`.
The skill has `name` and `description` metadata. No executable adapter or native
named-agent registration is needed. Instructions load into the current
conversation; use the template again in a new session.

Pi discovers these resources from `~/.pi/agent/prompts/*.md` and
`~/.pi/agent/skills/**/SKILL.md`. These are user resources, available across
projects. Review project instructions and trust separately. If another extension
owns the same slash command, resolve that collision before use. Custom agent-dir
overrides and disabled resource discovery require operator configuration outside
the kit. `/reload` refreshes resources in an open session.

## Optional extensions

Review the pinned upstream source and configure each extension outside lead-kit.
Upstream Pi package-manager commands are `pi install npm:pi-subagents@0.79.1` and
`pi install npm:pi-goal-x@0.32.3`. They execute third-party package code when Pi
loads it. This kit doesn't run them. After setup, select either or both IDs in
the example's `capabilities`, preview, and reinstall from the same config path.
Missing tools block that integration action; ordinary local work can continue.

### pi-subagents 0.79.1

The exact package is [nicobailon/pi-subagents](https://github.com/nicobailon/pi-subagents/tree/v0.79.1),
published as [`pi-subagents@0.79.1`](https://registry.npmjs.org/pi-subagents/0.79.1).
Its peer `@earendil-works/pi-ai >=0.86.1` admits 1.0.0; the coding-agent,
agent-core, tui and typebox peers use `*`. Its undici 8.10.2 dependency requires
Node 22.19+. The npm manifest loads `index.js`, skills and prompts; the source
manifest loads `index.ts`. The package ships builtin agents. Custom child agents
live in `~/.pi/agent/agents/**/*.md` or trusted project `.pi/agents/**/*.md`.
Lead-kit installs neither child agents nor package resources.

The verified [tool schema](https://github.com/nicobailon/pi-subagents/blob/v0.79.1/src/extension/schemas.ts)
puts `agent`, `task`, `async`, `action`, `id` and `message` at top level; management
and limits such as `timeoutMs`, `context`, `share` and `topic` go in `options`.
[Activation](https://github.com/nicobailon/pi-subagents/blob/v0.79.1/src/extension/tool-activation.ts)
may expose `subagents_enable({})` first. It enables delegation on the next model
request and starts no child. Delegate only with authorization.

The pack starts with a bounded foreground scout example. The
[tool reference](https://github.com/nicobailon/pi-subagents/blob/v0.79.1/docs/tool-reference.md)
defines async receipts, exact-id status/steer/resume, output references, retained
child eligibility and separate timeout, concurrency, depth and spawn limits.
Foreground children don't inherit ambient extensions. The builtin researcher and
evidence-auditor also require pi-web-access tools loaded in the child;
see [agent prerequisites](https://github.com/nicobailon/pi-subagents/blob/v0.79.1/docs/agents.md#web-research-prerequisites).
This pack supplies no remote reporting transport.

### pi-goal-x 0.32.3

The supplied [package page](https://pi.dev/packages/pi-goal-x) resolves to
[tmonk/pi-goal-x](https://github.com/tmonk/pi-goal-x/tree/v0.32.3), npm `pi-goal-x`.
Its [manifest](https://github.com/tmonk/pi-goal-x/blob/v0.32.3/package.json) loads
`extensions/goal.ts`. The ai, coding-agent and tui peers require
`>=0.83.0 <2.0.0`, and typebox requires `^1.3.11`; dev dependencies pin Pi 1.0.0.
Its own Node minimum is 22.15.0; Pi's 22.19.0 minimum still applies.
It has no pi-subagents dependency and owns its optional completion auditor.

The [core tools](https://github.com/tmonk/pi-goal-x/blob/v0.32.3/extensions/goal-core-tools.ts)
register `get_goal`, `create_goal` and `update_goal`. `get_goal` reads the focused
goal; `create_goal` creates and focuses a persistent goal only on explicit request.
`update_goal` accepts exactly one lifecycle status or continuation declaration.
`paused` stops immediately with a required reason; `blocked` has a separate
three-consecutive-turn policy. `complete` enters the completion flow and, when
enabled, independent auditing. Inspect its returned state before claiming success.
The [task tools](https://github.com/tmonk/pi-goal-x/blob/v0.32.3/extensions/goal-task-tools.ts)
use a confirmed flat parent-linked tree (at most 50 tasks) and evidence-bearing
task progress. Read the live schema before changing a task tree.

Use `/goal` to discuss and confirm, `/goal-focus` to select an existing goal,
`/goal-pause` to stop and `/goal-resume` to resume or take execution ownership.
Selection alone never activates a goal. Active goals continue automatically;
unset `maxAutonomousRuns` means unlimited. Have the operator choose an allowance
in `/goal-settings`. Strict ready/wait contracts are opt-in; waits retain their
identity/deadline and timers need Pi open. Allowances bound extension-started runs.
Within-run tool calls have no allowance cap. Focus is session-local; the default
pool is `.pi/goals`.
See the pinned [advanced semantics](https://github.com/tmonk/pi-goal-x/blob/v0.32.3/docs/advanced-usage.md).

## Evidence boundary

Offline tests exercise rendering, metadata, selection and installation in isolated
homes. Interfaces were checked against the tagged sources linked above and
[Pi 1.0.0](https://github.com/earendil-works/pi/tree/v1.0.0/packages/coding-agent).
Peer ranges admit Pi 1.0.0. Live extension loading, model calls, child delivery and
goal continuation haven't been exercised. No packages were installed for these checks.
