"""Lead module v1: resources are relative to this module, never Chief."""
import json
import os
from pathlib import Path
import re

SRC = Path(__file__).resolve().parent.parent

def read(path):
    return (SRC / path).read_text().strip()

def expand(text, values):
    # Resolve nested explicit placeholders, fail closed on unknowns or cycles.
    for _ in range(12):
        if not re.search(r'{{[A-Z_]+}}', text):
            return text
        text = re.sub(r'{{([A-Z_]+)}}', lambda m: values[m[1]], text)
    raise ValueError('cyclic composition')

def pack_values(packs):
    if not isinstance(packs, list) or not packs or len(set(packs)) != len(packs):
        raise ValueError('packs must be a nonempty unique list')
    result = {}
    for name in packs:
        if name not in ('engineering', 'research', 'life-admin'):
            raise ValueError('unknown practice pack')
        part = json.loads(read(f'practices/{name}/lead.json'))
        for key, value in part.items():
            if key in ('DOMAIN', 'DECISION_HEADING'):
                # Engineering keeps its established log vocabulary if attached.
                result.setdefault(key, value)
                if name == 'engineering':
                    result[key] = value
            else:
                result[key] = result.get(key, '') + ('\n' if key in result else '') + value
    return result

def owner_values(owner, technical=False):
    if not isinstance(owner, dict):
        raise ValueError('owner must be explicit')
    if owner.get('mode') == 'principal' and set(owner) == {'mode', 'style'}:
        style = owner['style']
        if not isinstance(style, str) or not style.strip() or '{{' in style:
            raise ValueError('principal style must be explicit plain text')
        return dict(OWNER_NAME='the principal', OWNER_SENTENCE='The principal',
                    OWNER_SHORT='principal', OWNER_LOG='reports directly to principal',
                    OWNER='- **The principal directly.** No chief is required. Speak in outcomes, '
                          'not mechanics. Principal style: ' + style,
                    PRINCIPAL_UPDATE='record the outcome in your log, including',
                    DELIVERY='To escalate, ask the principal directly in this conversation. '
                             'Use their style: outcomes, not mechanics. Ask only when a decision '
                             'is needed; record blocked work and continue independent work.')
    if owner.get('mode') != 'agent' or set(owner) != {'mode', 'pointer', 'label'}:
        raise ValueError('owner must be principal (style) or agent (pointer, label)')
    pointer, label = owner['pointer'], owner['label']
    if (not isinstance(pointer, str) or not Path(pointer).is_absolute()
            or any(x in pointer for x in ('\n', '`', '{{'))):
        raise ValueError('owner pointer must be an absolute path')
    if not isinstance(label, str) or not re.fullmatch(r'[A-Za-z][A-Za-z -]{0,60}', label):
        raise ValueError('invalid owner label')
    if technical:
        return dict(OWNER_NAME='the chief', OWNER_SENTENCE='The chief', OWNER_SHORT='chief',
                    OWNER_LOG=f'chief: see {pointer}',
                    OWNER=f'- **The chief of staff.** Read its current session id from `{pointer}` every time\n'
                          '  you send it something, because the chief can move to a fresh session. Escalations and milestone\n'
                          '  reports go there, and nothing else does.',
                    PRINCIPAL_UPDATE='send the chief one short message saying',
                    DELIVERY='To escalate, make one `session.send` to the chief session (the id in `chief.json`) with\n'
                             '`returnResult: true`. Write it so\nthe chief can pass it to the principal in two spoken sentences:')
    return dict(OWNER_NAME='the reporting agent', OWNER_SENTENCE='The reporting agent',
                OWNER_SHORT='reporting agent', OWNER_LOG=f'agent owner ({label}): see {pointer}',
                OWNER=f'- **Agent session: {label}.** Re-read `{pointer}` for every send. '
                      'Use its existing `session` and `directory` fields, never a cached id. '
                      'Send escalations and milestones only.',
                PRINCIPAL_UPDATE='notify the reporting agent briefly of',
                DELIVERY='To escalate, use `session.send` to the freshly resolved owner session and '
                         'directory, with `returnResult: true`. Its reply returns automatically. '
                         'Do not send an acknowledgement that creates a reply loop. Write for the '
                         'principal in outcomes, with evidence last:')

OWNER_SAFETY = ('## Reporting fallback\n\nFor agent-session reporting, re-read the live pointer '
                'before every send. It must contain a nonempty `session` and absolute `directory`. '
                'If missing, invalid, ambiguous or unavailable, log the blocked escalation and ask '
                'the principal directly; never guess, title-search, impersonate an owner or silently '
                'switch targets. Uncertain delivery is not permission to resend. In principal mode '
                'reply here and log the decision; no agent pointer is needed.')

def lead_prompt(values):
    values = {**LEAD_HOST_DEFAULTS, **values, 'LOG_TEMPLATE': (SRC / 'kits/lead/log.template.md').read_text().rstrip()}
    return expand(read('kits/lead/core.md'), values) + '\n\n' + OWNER_SAFETY + '\n\n' + read('kits/shared/docket.md') + '\n\n' + read('kits/shared/fleet.md')

LEAD_HOST_DEFAULTS = {
    'GOAL_INTRO': 'Own the outcome set by {{OWNER_NAME}} across turns until verified. Native goal activation requires a supported host and explicit operator binding; never infer it from these instructions.',
    'WORKER_SEND': 'the `openchamber` tool\'s `session.send`: an explicit `model` and `variant`,\n  and `returnResult: true` so its result comes back to you.',
    'SELF_ID': 'echo $OPENCODE_SESSION_ID', 'QUESTION_SEND': 'openchamber tool (session.send, returnResult true)',
    'RELAY_TOOL': '`session.send`',
}

def load_lead_config(path):
    config = json.loads(Path(path).read_text())
    if (not isinstance(config, dict) or set(config) != {'version', 'agent', 'packs', 'owner'}
            or type(config['version']) is not int or config['version'] != 1):
        raise ValueError('lead config requires version=1, agent, packs, owner only')
    if not isinstance(config['agent'], str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,47}', config['agent']):
        raise ValueError('invalid agent name')
    if config['agent'] in ('lead', 'chief-of-staff', 'shape', 'checkpoint'):
        raise ValueError('standalone agent must not collide with technical defaults')
    values = {**pack_values(config['packs']), **owner_values(config['owner']),
              'INTRO': 'You are the lead for one outcome. Own its plan, bounded workers, decisions, '
                       'verification and log. The principal is authoritative. Keep the agreed outcome intact.',
              'MODEL_POLICY': '## Optional shared policy\n\nUse an explicitly supplied model policy or routing service if available. '
                              'No chief memory is required. Without one, choose an available model within '
                              'current permissions. Paid use requires explicit project approval. '
                              'Checkpoint before moving a worker; never silently lower the lead quality tier.',
              'WORKER_ROUTING': 'Use a supplied routing service if configured; otherwise choose an available authorized model.',
              'LEAD_AGENT': config['agent'], 'CHECKPOINT_NAME': config['agent'] + '-checkpoint'}
    return config, values
