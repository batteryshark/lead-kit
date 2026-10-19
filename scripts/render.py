"""Static composition from a shipped, explicit registry."""
import json
from pathlib import Path
import re

SRC = Path(__file__).resolve().parent.parent
HOSTS = ('opencode', 'claude', 'codex')
ID = r'[a-z][a-z0-9-]{0,47}'
RESERVED = {'lead', 'chief-of-staff', 'shape', 'checkpoint', 'build', 'plan',
            'general', 'explore', 'default', 'worker', 'explorer'}


def read(path):
    target = SRC / path
    if not target.resolve().is_relative_to(SRC) or target.is_symlink():
        raise ValueError('resource must stay inside the kit')
    return target.read_text().strip()


def expand(text, values):
    for _ in range(12):
        if not re.search(r'{{[A-Z_]+}}', text):
            return text
        text = re.sub(r'{{([A-Z_]+)}}', lambda m: values[m[1]], text)
    raise ValueError('cyclic composition')


def ids(value, label, allowed):
    if (not isinstance(value, list) or any(not isinstance(x, str) for x in value)
            or len(set(value)) != len(value) or any(x not in allowed for x in value)):
        raise ValueError(f'{label} must be a unique list of known IDs: {", ".join(sorted(allowed))}')
    return value


def registry():
    packs = json.loads(read('packs.json'))
    if not isinstance(packs, list):
        raise ValueError('pack registry must be a list')
    seen = set()
    for p in packs:
        if (not isinstance(p, dict) or set(p) != {'id', 'kind', 'hosts', 'requires', 'content', 'description'}
                or not isinstance(p['id'], str) or not re.fullmatch(ID, p['id'])
                or p['id'] in seen or p['kind'] not in ('practice', 'capability')
                or not isinstance(p['description'], str) or not p['description'].strip()):
            raise ValueError('invalid or duplicate pack manifest')
        seen.add(p['id'])
        ids(p['hosts'], 'pack hosts', HOSTS)
        if not p['hosts'] or not isinstance(p['content'], str):
            raise ValueError('pack requires hosts and content')
        prefix = 'practices/' if p['kind'] == 'practice' else 'capabilities/'
        if p['content'] != f"{prefix}{p['id']}/instructions.md":
            raise ValueError('pack content must be <kind-directory>/<id>/instructions.md')
        content = read(p['content'])
        if not content:
            raise ValueError('empty pack content')
        if set(re.findall(r'{{([A-Z_]+)}}', content)) - {'LEAD_AGENT', 'CHECKPOINT_NAME', 'OWNER', 'OWNER_LOG'}:
            raise ValueError('unknown pack placeholder')
    for p in packs:
        ids(p['requires'], 'pack prerequisites', seen)
        if p['kind'] == 'practice' and any(
                x['kind'] != 'practice' for x in packs if x['id'] in p['requires']):
            raise ValueError('practice prerequisites must be practices')
    ordered, visiting = [], set()

    def visit(p):
        if p['id'] in visiting:
            raise ValueError('cyclic pack dependencies')
        if p in ordered:
            return
        visiting.add(p['id'])
        for dep in p['requires']:
            visit(next(x for x in packs if x['id'] == dep))
        visiting.remove(p['id'])
        ordered.append(p)

    for p in packs:
        visit(p)
    return ordered


def plain(value, label):
    if (not isinstance(value, str) or not value.strip() or '{{' in value
            or any(ord(c) < 32 for c in value) or '`' in value):
        raise ValueError(f'{label} must be nonempty single-line plain text')
    return value


def owner_values(owner, capabilities):
    if not isinstance(owner, dict):
        raise ValueError('owner must be explicit')
    if owner.get('mode') == 'principal' and set(owner) == {'mode', 'style'}:
        style = plain(owner['style'], 'principal style')
        return {'OWNER': 'Report to the principal in this conversation. ' + style,
                'OWNER_LOG': 'reports directly to principal'}
    if owner.get('mode') != 'agent' or set(owner) != {'mode', 'pointer', 'label', 'integration'}:
        raise ValueError('owner: use principal (style) or agent (pointer, label, integration)')
    if owner['integration'] != 'openchamber' or 'openchamber' not in capabilities:
        raise ValueError('agent owner requires integration="openchamber" and the openchamber capability; use principal otherwise')
    pointer = plain(owner['pointer'], 'owner pointer')
    if not Path(pointer).is_absolute() or '..' in Path(pointer).parts:
        raise ValueError('owner pointer must be an absolute path without ..')
    label = plain(owner['label'], 'owner label')
    return {'OWNER': f'Report milestones and escalations to {label}. Before every send, read `{pointer}`. '
            'Require a nonempty `session` and absolute `directory` in that JSON file. '
            'Use the openchamber tool action `session.send` with those sessionId and directory '
            'parameters and returnResult: true. The reply arrives automatically. '
            'If the pointer or tool is unavailable or invalid, log the blocked delivery and ask '
            'the principal here. Never guess, title-search or resend uncertain delivery. '
            'Do not acknowledge replies in a message loop.',
            'OWNER_LOG': f'agent owner {label}: {pointer} (openchamber)'}


def load_lead_config(path):
    config = json.loads(Path(path).read_text())
    if isinstance(config, dict) and config.get('version') == 1:
        raise ValueError('config v1 migration: set version=2; rename packs to practices; add explicit hosts and capabilities lists; agent owners also need integration="openchamber" and that capability. No files changed.')
    if (not isinstance(config, dict) or set(config) != {'version', 'agent', 'hosts', 'practices', 'capabilities', 'owner'}
            or type(config['version']) is not int or config['version'] != 2):
        raise ValueError('config requires version=2, agent, hosts, practices, capabilities, owner only')
    name = config['agent']
    if not isinstance(name, str) or not re.fullmatch(ID, name) or name in RESERVED:
        raise ValueError('invalid or reserved agent name')
    ids(config['hosts'], 'hosts', HOSTS)
    if not config['hosts']:
        raise ValueError('hosts must explicitly select at least one host')
    packs = registry()
    for kind, field in [('practice', 'practices'), ('capability', 'capabilities')]:
        ids(config[field], field, [p['id'] for p in packs if p['kind'] == kind])
    selected = set(config['practices'] + config['capabilities'])
    for p in packs:
        if p['id'] in selected:
            if not set(p['requires']) <= selected:
                raise ValueError(f"{p['id']} requires explicit selection of: {', '.join(p['requires'])}")
            if not set(config['hosts']) <= set(p['hosts']):
                raise ValueError(f"{p['id']} supports hosts: {', '.join(p['hosts'])}")
    values = {**owner_values(config['owner'], config['capabilities']),
              'LEAD_AGENT': name, 'CHECKPOINT_NAME': name + '-checkpoint',
              'PRACTICES': '\n\n'.join(read(p['content']) for p in packs if p['kind'] == 'practice' and p['id'] in selected),
              'CAPABILITIES': '\n\n'.join(read(p['content']) for p in packs if p['kind'] == 'capability' and p['id'] in selected)}
    return config, values


def lead_prompt(values, host):
    return expand(read('kits/lead/core.md'), {
        **values, 'HOST': read(f'kits/lead/hosts/{host}-guidance.md'),
        'LOG_TEMPLATE': (SRC / 'kits/lead/log.template.md').read_text().rstrip()}) + '\n'
