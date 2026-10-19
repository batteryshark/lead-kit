# Configuration and pack contract

Config version 2 accepts exactly `version`, `agent`, `hosts`, `practices`,
`capabilities` and `owner`. Lists must contain unique known IDs. `hosts` must
contain at least one of `opencode`, `claude`, `codex`, `pi`; the pack lists may be empty.
A selected pack must support every selected host. Prerequisites must be selected
explicitly; the renderer never adds a pack for you. Unknown fields fail validation.

Agent names start with a lowercase letter, followed by lowercase letters, digits
or hyphens, up to 48 characters. Built-in host agent IDs and the kit's former
reserved names are rejected; `scripts/render.py` lists the reserved set.

## Reporting

Principal mode uses `{"mode":"principal","style":"Short outcomes."}` and replies
in the current conversation. Style and labels must be single-line plain text.

[examples/agent.json](../examples/agent.json) binds agent-owner reporting to the
`openchamber` pack. Set its absolute `owner.pointer` to an operator-controlled JSON
file containing a nonempty `session` and an absolute `directory`. The lead
re-reads the pointer before each `session.send`; the installer does not read it
or contact the destination. The blank [owner template](../examples/owner.json)
needs real values before use. Invalid pointers or unavailable delivery tools
produce a logged blocker and a request to the principal in the current conversation.

A2A communication does not implicitly select the reporting channel. No agent-owner
binding is shipped for Claude, Codex, Pi or A2A. Use principal mode on those paths.

## Register a pack

Add `practices/<id>/instructions.md` or `capabilities/<id>/instructions.md`, then
add one entry to the repository's `packs.json` list:

```json
{
  "id": "research",
  "kind": "practice",
  "hosts": ["opencode", "claude", "codex"],
  "requires": [],
  "content": "practices/research/instructions.md",
  "description": "Source evidence and bounded synthesis"
}
```

Every field shown is required; extra fields are rejected. IDs use the agent-name
character rules and are unique across both kinds. `kind` is `practice` or
`capability`. The content path must match the kind directory and ID exactly.
Content must be nonempty and inside this repository. `hosts` is a nonempty list;
`requires` names other registered packs. Cycles and unknown prerequisites fail.
Practice prerequisites must also be practices.

Composition is core, selected host guidance, selected practices, then selected
capabilities. Within each pack phase, registry order breaks ties and dependencies
come first. Config list order does not change output. Supported placeholders are
`{{LEAD_AGENT}}`, `{{CHECKPOINT_NAME}}`, `{{OWNER}}` and `{{OWNER_LOG}}`;
unknown placeholders fail rendering. Pack content does not grant tool permissions.
Keep their scope additive and their fallback explicit when a selected tool is absent.

The registry is read only from this checkout. Pack text is statically included;
there is no runtime discovery or automatic integration setup. A new integration
needs a verified tool contract before it can name calls or declare dependencies.

## Current dependencies

`a2a` uses the exposed `a2a_create`, `a2a_send`, `a2a_list` and `a2a_read`
contract. `openchamber` uses the exposed `openchamber` action/parameters contract.
They do not require each other. Both currently target OpenCode.

`runway` targets OpenCode and requires `openchamber`: its `prepare` operation
returns OpenChamber dispatch arguments, and its ledger binds the returned session.
Its entry instructs the lead to read the installed `routing/WORKFLOW.md` before
calling `usage`, `plan`, `prepare`, `bind` or `finish`. The installed workflow
supplies request syntax and policy; this kit ships no quota service or policy data.

`pi-subagents` and `pi-goal-x` each target only Pi, with no pack dependencies.
Both require the corresponding operator-installed extension. See [Pi](pi.md)
for pinned interfaces and prerequisites. A mixed-host config with either pack
fails validation before writes; use separate configs for those integrations.

`docket` and `fleet` work as optional guidance on all four hosts. Each requires
an operator-configured installation and its usage guide. Fleet's service
instructions apply to macOS. Pack selection does not validate the operating
system or authorize service startup.

## Host adapters and checks

Each host has a wrapper and a `*-guidance.md` file under `kits/lead/hosts/`.
Wrappers supply native output syntax; guidance names only that host's worker and
checkpoint behavior. `scripts/install-lead.py` owns destinations and checkpoint
wrapping. A new host needs explicit registration there and in `render.HOSTS`,
plus pack applicability updates and lifecycle/content tests.

Extend `tests/test_standalone.py` to assert a new pack's substantive instructions
appear when selected and disappear when unselected. Test prerequisites, host
rejection and deterministic output, then preview the config with `--print`.
Run the test command in the root README. Python 3.11+ also parses the
Codex profile with `tomllib`; Python 3.9 checks the serialized instruction string.

Install state tracks the prior agent name for one canonical config path. Known
managed output paths are derived in code, including the former Codex checkpoint
location, so state cannot supply arbitrary deletion paths. Legacy ownership
markers are recognized for migration. Keep the config path stable across edits;
uninstall the old config before moving it. Separate configs should use distinct
agent names.

## Host references

- [OpenCode V2 agents](https://opencode.ai/v2/docs/agents),
  [commands](https://opencode.ai/v2/docs/commands) and
  [skills](https://opencode.ai/v2/docs/skills).
- [Claude Code custom agents](https://code.claude.com/docs/en/sub-agents) and
  [skills](https://code.claude.com/docs/en/skills).
- [Codex profiles](https://developers.openai.com/codex/config-file/config-advanced/#profiles),
  [subagents](https://developers.openai.com/codex/agent-configuration/subagents) and
  [skills](https://developers.openai.com/codex/build-skills).
- [Pi 1.0.0 prompt templates](https://github.com/earendil-works/pi/blob/v1.0.0/packages/coding-agent/docs/prompt-templates.md),
  [skills](https://github.com/earendil-works/pi/blob/v1.0.0/packages/coding-agent/docs/skills.md)
  and [configuration](https://github.com/earendil-works/pi/blob/v1.0.0/packages/coding-agent/docs/configuration.md).
