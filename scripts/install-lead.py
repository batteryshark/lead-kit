#!/usr/bin/env python3
"""Preflight every output and stale managed file before changing anything."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from render import HOSTS, ID, expand, lead_prompt, load_lead_config, read, registry
from install_paths import DestinationRoot


def marker(name, key):
    return f'managed by lead-kit/install.sh; installation {key}; lead {name}'


def owned(path, name, key):
    lines = path.read_text().splitlines()
    label = marker(name, key)
    return f'<!-- {label} -->' in lines or f'# {label}' in lines


def paths(home, name):
    checkpoint = name + '-checkpoint'
    return {
        'opencode': [home / f'.config/opencode/agents/{name}.md',
                     home / f'.config/opencode/commands/{checkpoint}.md'],
        'claude': [home / f'.claude/agents/{name}.md', home / f'.claude/skills/{checkpoint}/SKILL.md'],
        'codex': [home / f'.codex/{name}.config.toml', home / f'.agents/skills/{checkpoint}/SKILL.md'],
        'pi': [home / f'.pi/agent/prompts/{name}.md', home / f'.pi/agent/skills/{checkpoint}/SKILL.md'],
        'legacy': [home / f'.codex/skills/{checkpoint}/SKILL.md']}


def render_outputs(home, config, values, key):
    name = config['agent']
    checkpoint = expand(read('kits/lead/skills/checkpoint.md'), values)
    outputs = {}
    for host in HOSTS:
        if host not in config['hosts']:
            continue
        prompt = lead_prompt(values, host)
        # JSON basic strings are also TOML basic strings for these prompt characters.
        toml_prompt = json.dumps(prompt, ensure_ascii=False)
        template = 'codex.toml' if host == 'codex' else host + '.md'
        label = '# ' + marker(name, key) if host == 'codex' else f'<!-- {marker(name, key)} -->'
        agent_text = expand(read(f'kits/lead/hosts/{template}'),
                            {**values, 'PROMPT': prompt, 'TOML_PROMPT': toml_prompt, 'MARKER': label}) + '\n'
        if host == 'opencode':
            checkpoint_text = (f'---\ndescription: Checkpoint this lead before handover\nagent: {name}\nsubagent: false\n---\n'
                               f'{label}\n\n{checkpoint}\n\nArguments: $ARGUMENTS\n')
        else:
            checkpoint_text = (f'---\nname: {values["CHECKPOINT_NAME"]}\n'
                               'description: Save project state before handover or when context grows long\n---\n'
                               f'<!-- {marker(name, key)} -->\n\n{checkpoint}\n')
            if host == 'pi':
                checkpoint_text += (f'\nFor a fresh Pi session, start `pi` in this project, then invoke '
                                    f'`/{name} Read LEAD.md and resume the recorded next action.`\n')
        agent_path, checkpoint_path = paths(home, name)[host]
        outputs[agent_path] = agent_text
        outputs[checkpoint_path] = checkpoint_text
    return outputs


def record(home, key, name, hosts):
    return dict(version=2, installation=key, agent=name, hosts=hosts,
                outputs=[str(p.relative_to(home)) for host in hosts for p in paths(home, name)[host]])


def load_records(home, state, destination):
    """Read only the small registry, never probe other installations' host roots."""
    records = {}
    for path in sorted(state.parent.glob('*.json')):
        destination.validate_all([path])
        if not re.fullmatch(r'[0-9a-f]{24}', path.stem):
            raise ValueError(f'invalid lead-kit record filename: {path}')
        data = json.loads(path.read_text())
        error = f'invalid lead-kit install state: {path}; restore the record before retrying'
        if (not isinstance(data, dict) or not isinstance(data.get('agent'), str)
                or not re.fullmatch(ID, data['agent']) or type(data.get('version')) is not int):
            raise ValueError(error)
        if data['version'] == 1 and set(data) == {'version', 'agent'}:
            if path == state:
                raise ValueError(f'legacy lead-kit install state: {path}; move reviewed legacy outputs '
                                 'and this record aside before reinstalling')
        else:
            hosts = data.get('hosts')
            if (not isinstance(hosts, list) or not hosts
                    or any(not isinstance(h, str) or h not in HOSTS for h in hosts)
                    or len(set(hosts)) != len(hosts)
                    or data != record(home, path.stem, data['agent'], hosts)):
                raise ValueError(error)
        records[path.stem] = data
    return records


def replace(target, text):
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False) as f:
        temp = Path(f.name)
        try:
            f.write(text)
        except BaseException:
            temp.unlink()
            raise
    try:
        temp.replace(target)
    finally:
        if temp.exists():
            temp.unlink()


def main(config_path, mode):
    if mode not in ('print', 'dry', 'install', 'uninstall'):
        raise ValueError('invalid install mode')
    config, values = load_lead_config(config_path)
    destination = DestinationRoot(os.environ['HOME'])
    home, name = destination.path, config['agent']
    key = hashlib.sha256(str(Path(config_path).resolve()).encode()).hexdigest()[:24]
    state = home / f'.local/state/lead-kit/{key}.json'
    destination.validate_all([state])
    records = load_records(home, state, destination)
    previous = records.get(key)
    recorded = {home / p for p in previous['outputs']} if previous else set()
    outputs = render_outputs(home, config, values, key)
    intended = set(outputs) | recorded
    destination.validate_all(sorted(intended))
    for other_key, data in records.items():
        if other_key == key:
            continue
        if data['version'] == 1:
            reserved = {p for group in paths(home, data['agent']).values() for p in group}
        else:
            reserved = {home / p for p in data['outputs']}
        if intended & reserved:
            other_state = state.parent / f'{other_key}.json'
            raise ValueError(f'output reserved by another config installation: {other_state}; uninstall '
                             'using its original config, or move reviewed legacy outputs and record aside')
    for target in sorted(intended):
        if target.exists() and (target not in recorded or not owned(target, previous['agent'], key)):
            raise ValueError(f'not owned by this installation: {target}; move the reviewed file aside '
                             'before retrying (name-only and legacy markers cannot establish ownership)')
    stale = sorted(p for p in recorded if p.exists() and (p not in outputs or mode == 'uninstall'))
    if mode in ('print', 'dry'):
        for target in stale:
            print(f'would remove {target}')
        for target, text in outputs.items():
            print(f'=== {target}\n{text}' if mode == 'print' else f'would write {target}')
        print(f'would track installation in {state}')
        return
    # Record the new identity last; individual replacements are atomic, the set is not.
    for target, text in outputs.items():
        if mode == 'install':
            replace(target, text)
            print(f'installed {target}')
    for target in stale:
        target.unlink()
        print(f'removed {target}')
    if mode == 'install':
        hosts = [h for h in HOSTS if h in config['hosts']]
        replace(state, json.dumps(record(home, key, name, hosts), sort_keys=True) + '\n')
    elif state.exists():
        state.unlink()


if __name__ == '__main__':
    try:
        if sys.argv[1:] == ['--list-packs']:
            for p in registry():
                print(f"{p['kind']} {p['id']} | hosts: {', '.join(p['hosts'])} | requires: {', '.join(p['requires']) or 'none'} | {p['description']}")
        else:
            main(*sys.argv[1:])
    except (ValueError, KeyError, OSError, TypeError) as e:
        sys.exit(f'install.sh: {e}')
