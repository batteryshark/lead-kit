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


def marker(name):
    return f'managed by lead-kit/install.sh; lead {name}'


def owned(path, name):
    text = path.read_text()
    for label in (marker(name), f'managed by chief-of-staff/install.sh; standalone lead {name}'):
        if f'<!-- {label} -->' in text.splitlines() or f'# {label}' in text.splitlines():
            return True
    return False


def paths(home, name):
    checkpoint = name + '-checkpoint'
    return {
        'opencode': [home / f'.config/opencode/agents/{name}.md',
                     home / f'.config/opencode/commands/{checkpoint}.md'],
        'claude': [home / f'.claude/agents/{name}.md', home / f'.claude/skills/{checkpoint}/SKILL.md'],
        'codex': [home / f'.codex/{name}.config.toml', home / f'.agents/skills/{checkpoint}/SKILL.md'],
        'legacy': [home / f'.codex/skills/{checkpoint}/SKILL.md']}


def render_outputs(home, config, values):
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
        label = '# ' + marker(name) if host == 'codex' else f'<!-- {marker(name)} -->'
        agent_text = expand(read(f'kits/lead/hosts/{template}'),
                            {**values, 'PROMPT': prompt, 'TOML_PROMPT': toml_prompt, 'MARKER': label}) + '\n'
        if host == 'opencode':
            checkpoint_text = (f'---\ndescription: Checkpoint this lead before handover\nagent: {name}\nsubagent: false\n---\n'
                               f'{label}\n\n{checkpoint}\n\nArguments: $ARGUMENTS\n')
        else:
            checkpoint_text = (f'---\nname: {values["CHECKPOINT_NAME"]}\n'
                               'description: Save project state before handover or when context grows long\n---\n'
                               f'<!-- {marker(name)} -->\n\n{checkpoint}\n')
        agent_path, checkpoint_path = paths(home, name)[host]
        outputs[agent_path] = agent_text
        outputs[checkpoint_path] = checkpoint_text
    return outputs


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
    previous = name
    if state.exists():
        data = json.loads(state.read_text())
        if (not isinstance(data, dict) or set(data) != {'version', 'agent'}
                or type(data['version']) is not int or data['version'] != 1
                or not isinstance(data['agent'], str) or not re.fullmatch(ID, data['agent'])):
            raise ValueError('invalid lead-kit install state; restore it before reinstalling')
        previous = data['agent']
    outputs = render_outputs(home, config, values)
    candidates = {p: n for n in (previous, name) for group in paths(home, n).values() for p in group}
    destination.validate_all([*candidates, state])
    for target in outputs:
        if target.exists() and not owned(target, name):
            raise ValueError(f'not owned by this lead: {target}')
    stale = []
    for target, owner in candidates.items():
        if target not in outputs or mode == 'uninstall':
            if target.exists() and owned(target, owner):
                stale.append(target)
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
        replace(state, json.dumps({'version': 1, 'agent': name}, sort_keys=True) + '\n')
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
