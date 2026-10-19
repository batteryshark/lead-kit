# Lead kit

<p><a href="assets/workstack-mark-full.png"><img src="assets/workstack-mark.png" alt="A beaver in a hard hat holding a project map" width="160"></a></p>

Lead kit installs a custom project-lead agent and a named checkpoint command or
skill for OpenCode, Claude Code or Codex. The lead plans work, implements changes
or delegates bounded jobs, checks results and keeps decisions in `LEAD.md`.
Checkpointing saves enough state for the next session to resume.

For a database migration, give the lead the schema change, compatibility rules
and acceptance tests. It can inspect the code, plan the migration, implement and
test it, then record the evidence and rollback steps. With worker tools available,
it can assign implementation and review separately. It asks you before changing
scope or publishing the result.

## Choose your lead

One JSON config selects the agent name, hosts, practice packs and capabilities.
Start with [examples/principal.json](examples/principal.json), which reports to
you in the current conversation:

```json
{
  "version": 2,
  "agent": "project-lead",
  "hosts": ["opencode"],
  "practices": ["engineering"],
  "capabilities": [],
  "owner": {
    "mode": "principal",
    "style": "Short outcomes with evidence on request."
  }
}
```

Use `claude` or `codex` for another host, or list several hosts explicitly.
Practices are `engineering`, `research` and `life-admin`; an empty list uses
only the core project-leading instructions. Capabilities are opt-in:

- `a2a`: peer messages and authorized local workers.
- `openchamber`: session operations, agent-owner reporting and requested handoffs.
- `runway`: Runway / Tarmac quota routing; requires `openchamber`.
- `docket`: guidance for an operator-configured scheduler.
- `fleet`: guidance for an operator-configured macOS service registry.

The first three capability packs target OpenCode with their corresponding tools
already configured. A2A and OpenChamber can be selected independently. Missing
tools block the requested integration action while local project work continues.
The installer validates selections without contacting hosts or installing tools.

## Preview and install

From this checkout, with Bash and Python 3.9+ available:

```sh
cp examples/principal.json my-lead.json
bash install.sh --list-packs
bash install.sh --lead-config my-lead.json --print
bash install.sh --lead-config my-lead.json --dry-run
bash install.sh --lead-config my-lead.json
```

Edit `my-lead.json` before previewing to change the selections. `--print` shows
the complete configured output and any stale managed files to remove. `--dry-run`
lists destinations. Both modes leave the destination unchanged.

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

### Managed files

The installer uses the selected `HOME` and writes two resources per host:

- OpenCode: `.config/opencode/agents/<agent>.md` and
  `.config/opencode/commands/<agent>-checkpoint.md`.
- Claude Code: `.claude/agents/<agent>.md` and
  `.claude/skills/<agent>-checkpoint/SKILL.md`.
- Codex: `.codex/<agent>.config.toml` (a named CLI profile) and
  `.agents/skills/<agent>-checkpoint/SKILL.md`.

It records the installed name under `.local/state/lead-kit/`, keyed by config
path. Reinstall from the same config path after changing hosts, packs or the
agent name: previous managed outputs are removed. To undo the install:

```sh
bash install.sh --lead-config my-lead.json --uninstall
```

Uninstall before moving or copying a config to a different path. Edit the source
or config and reinstall instead of editing managed files. Unowned output files
and symlinks below `HOME` block conflicting operations; all candidate paths are
checked before writes. Unowned stale files are retained. Empty directories may
remain. Files are replaced individually, so an I/O failure can leave a partial
install; concurrent path replacement is outside the guard's protection.

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
uses `HOME` directly, irrespective of `XDG_CONFIG_HOME` or `CODEX_HOME`.

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
