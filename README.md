# Lead kit

<p><a href="assets/workstack-mark-full.png"><img src="assets/workstack-mark.png" alt="A beaver in a hard hat holding a project map" width="160"></a></p>

Lead kit installs a project-lead agent that orchestrates work from a request
through completion in OpenCode, Claude Code, Codex or Pi 1.0. It turns the agreed
outcome into a plan, allocates the time and resources you've assigned, and
distributes bounded jobs when worker tools are available. The lead coordinates
dependencies and merges, resolves overlapping changes, and verifies the combined
result. When findings or resource limits call for a different approach, it brings
you the decision and updates the plan. It can also do the work itself.

For a database migration, give the lead the schema change, compatibility rules
and acceptance tests. The lead can split implementation and review between
workers, reconcile their changes, and check upgrade and rollback together. If
the old reader can't remain compatible, it raises that finding before proceeding.
Decisions and verification evidence go in `LEAD.md`; the installed checkpoint
command or skill saves the next action for a successor session.

## Preview and install

From this checkout, with Bash 3.2+ and Python 3.9+ available:

```sh
bash install.sh --preset opencode --print
bash install.sh --preset opencode
```

Replace `opencode` with `claude`, `codex` or `pi` for your host. Each preset
installs `project-lead` with engineering practice and reports to you in the current
conversation. Only the chosen host receives files. `--print` shows the complete
output; `--dry-run` lists destinations. Both are nonmutating, including on reinstall.

In your engineering project's folder, put the agreed outcome and constraints in
`PROJECT.md`. Select `project-lead` in OpenCode, run
`claude --agent project-lead` in Claude Code, or use
`codex --profile project-lead` in Codex. Then give it a concrete task:

> Add the orders-table migration described in PROJECT.md. Keep the old reader
> working, test upgrade and rollback, and maintain LEAD.md. Ask me before changing
> the compatibility requirements or publishing anything.

Before handover, invoke `/project-lead-checkpoint` in OpenCode or Claude Code,
or `$project-lead-checkpoint` in Codex. A `fresh` request saves the handover and
asks you to start a successor unless a selected integration supports that action.

### Pi 1.0

Have Pi 1.0.0 (`@earendil-works/pi-coding-agent`) and Node.js 22.19+ set up
outside this kit, with your chosen model available:

```sh
bash install.sh --preset pi --print
bash install.sh --preset pi
```

Pi loads the lead as a prompt template in the main conversation. In your project
folder, start `pi`, then enter
`/project-lead Add the migration described in PROJECT.md and maintain LEAD.md.`
Use `/skill:project-lead-checkpoint` before handover, or append `fresh` for a
copyable successor brief. Run `/reload` if Pi was already open during install.
Load `/project-lead` again in each new conversation.

For delegation, separately review and set up
[pi-subagents 0.79.1](https://pi.dev/packages/pi-subagents). For explicitly requested
autonomous goals, review and set up [pi-goal-x 0.32.3](https://pi.dev/packages/pi-goal-x).
Select either or both through a saved config as described below. Package
installation, Pi settings and goal activation remain under your control. See
[Pi setup and interface evidence](docs/pi.md) for exact prerequisites and calls.

## Optional packs and saved configs

Practices add project methods: `engineering`, `research` and `life-admin`.
Capabilities add instructions for integrations you've configured separately.
The base agent plans against your stated resource limits; measured quota usage
requires a configured integration.

### OpenCode integrations

- `a2a`: peer messages and authorized local workers.
- `openchamber`: session operations, agent-owner reporting and requested handoffs.
- `runway`: the Runway admission/worker-ledger adapter that dispatches prepared
  OpenChamber arguments. Requires `openchamber` and the installed routing workflow.

### Pi extensions

For Pi 1.0, select either pack independently or use both:

- `pi-subagents`: bounded delegation using pi-subagents 0.79.1.
- `pi-goal-x`: explicitly requested persistent goals using pi-goal-x 0.32.3.

### External services

- [`tarmac`](https://github.com/batteryshark/tarmac): passive quota/usage awareness
  from its independent REST API. Works on any supported host with authorized HTTP
  access to the configured endpoint; it has no OpenChamber dependency.
- [`docket`](https://github.com/batteryshark/docket): optional scheduling through
  a separate project's API/CLI/MCP. A caller on another host may access the API,
  but Docket's current delivery adapter wakes OpenCode sessions. Pi, Claude and
  Codex wake delivery isn't supplied by this pack.

To customize, copy the preset for your host and edit that saved file. If you've
already installed the preset, first run `bash install.sh --preset opencode --uninstall`
(using your host) so the new config can own the same agent name:

```sh
cp presets/opencode.json my-lead.json
bash install.sh --list-packs
bash install.sh --lead-config my-lead.json --print
bash install.sh --lead-config my-lead.json --dry-run
bash install.sh --lead-config my-lead.json
```

The JSON selects the agent name, hosts, practice IDs, capability IDs and reporting
owner. For Pi, copy `presets/pi.json` and set `capabilities` to `["pi-subagents"]`,
`["pi-goal-x"]` or both. Empty pack lists use only the core and host guidance.
Every selected pack must support every selected host; use separate configs for
host-specific capabilities. Missing tools block that integration action while
local work continues. The installer never contacts hosts or installs integrations.

Use exactly one of `--preset HOST` and `--lead-config FILE`.
Separate config paths have separate installation identities.
See [the configuration contract](docs/packs.md) for examples and service API details.

### Managed files

The installer uses the selected `HOME` and writes two resources per host:

- OpenCode: `.config/opencode/agents/<agent>.md` and
  `.config/opencode/commands/<agent>-checkpoint.md`.
- Claude Code: `.claude/agents/<agent>.md` and
  `.claude/skills/<agent>-checkpoint/SKILL.md`.
- Codex: `.codex/<agent>.config.toml` (a named CLI profile) and
  `.agents/skills/<agent>-checkpoint/SKILL.md`.
- Pi: `.pi/agent/prompts/<agent>.md` (the `/<agent>` template) and
  `.pi/agent/skills/<agent>-checkpoint/SKILL.md`.

It records the installed name, hosts and output paths under `.local/state/lead-kit/`,
keyed by the canonical config path. `--preset opencode` always uses the shipped
`presets/opencode.json`, including for preview and uninstall. Each output carries
that installation's identity; another config cannot claim it. Reinstall from the
same config path after changing hosts, packs or the agent name: recorded stale
outputs are removed. To undo an OpenCode preset install:

```sh
bash install.sh --preset opencode --uninstall
```

For a saved config, use `--lead-config my-lead.json --uninstall`. Uninstall before
moving the checkout or moving a config used for installation. Edit the source
or config and reinstall instead of editing managed files. Preflight checks selected
outputs, recorded outputs and install records before writes. Unowned files and
symlinks on those paths block changes; unrelated host roots are left alone. Empty
directories may remain. Files are replaced individually, so an I/O failure can
leave a partial install; concurrent path replacement is outside the guard's protection.

Older install records and name-only markers require manual migration: review and
move the old outputs and their record aside, then reinstall. The installer won't
adopt or remove those files automatically.

Version 1 configs receive a migration error: set `version` to `2`, rename `packs`
to `practices`, and add explicit `hosts` and `capabilities` lists. Agent-owner mode
also requires `integration: "openchamber"` and that capability. See
[the pack and configuration contract](docs/packs.md) for reporting and extension details.

## Extend it

`kits/lead/` contains the core, checkpoint and host adapters. `practices/` contains
project methods; `capabilities/` contains tool-specific instructions. `packs.json`
registers their content, host applicability and prerequisites. The existing
Bash/Python renderer composes selected instructions in a fixed order at install
time. Selected text stays in the agent's context; keeping rare, longer workflows
in host skills can save context until they are needed.

To add a pack, create its instructions, register it in `packs.json`, then test
selected and unselected output. [docs/packs.md](docs/packs.md) specifies the small
manifest contract and host adapter files.

## Requirements and checks

Bash 3.2+ and Python 3.9+ are required; the renderer uses the Python standard
library. Offline install tests pass on macOS with Bash 3.2 and Python 3.9.
Windows, WSL and Git Bash installation have not been exercised. The installer
uses `HOME` directly, irrespective of `XDG_CONFIG_HOME`, `CODEX_HOME` or
`PI_CODING_AGENT_DIR`. Use Pi's default agent directory for this installation.

```sh
python3 -B -m unittest discover -s tests -v
```

Tests check rendered behavior, pack validation, config changes, ownership guards
and install lifecycles in isolated homes. Host formats follow the linked
[official references](docs/packs.md#host-references); live host activation and
integration delivery remain untested.

## License and artwork

Source and documentation: [MIT](LICENSE). The existing marks are AI-generated
artwork, offered on MIT terms to the extent applicable, with no exclusive
copyright claim in AI-generated elements. See [RIGHTS.md](RIGHTS.md) and
[ATTRIBUTION.md](ATTRIBUTION.md).
