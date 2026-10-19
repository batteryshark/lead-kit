"""Offline fixtures: isolated homes under this checkout; no harness activation."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SRC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC / 'scripts'))
import render
from install_paths import DestinationRoot


class StandaloneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SRC, prefix='.test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.home = self.root / 'home'
        self.home.mkdir()
        self.env = {'PATH': os.environ['PATH'], 'HOME': str(self.home),
                    'TMPDIR': str(self.root), 'XDG_CONFIG_HOME': str(self.home / '.config'),
                    'XDG_DATA_HOME': str(self.home / '.local/share'),
                    'XDG_CACHE_HOME': str(self.home / '.cache'),
                    'PYTHONDONTWRITEBYTECODE': '1'}
        self.config = dict(version=2, agent='study-lead', hosts=['opencode'], practices=[], capabilities=[],
                           owner=dict(mode='principal', style='Short outcomes.'))

    def run_install(self, *args, config=None, config_name='config.json'):
        file = self.root / config_name
        file.write_text(json.dumps(self.config if config is None else config))
        return subprocess.run(['bash', str(SRC / 'install.sh'), '--lead-config', str(file), *args],
                              env=self.env, capture_output=True, text=True, timeout=15)

    def cli(self, *args):
        return subprocess.run(['bash', str(SRC / 'install.sh'), *args], env=self.env,
                              capture_output=True, text=True, timeout=15)

    def snapshot(self):
        return {str(p.relative_to(self.home)): p.read_bytes() for p in self.home.rglob('*') if p.is_file()}

    def tree_snapshot(self):
        return {str(p.relative_to(self.home)): ('link', os.readlink(p)) if p.is_symlink()
                else ('dir',) if p.is_dir() else ('file', p.read_bytes())
                for p in self.home.rglob('*')}

    def rejects_without_mutation(self, **kwargs):
        before = self.tree_snapshot()
        for mode in ((), ('--print',), ('--dry-run',), ('--uninstall',)):
            result = self.run_install(*mode, **kwargs)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertEqual(before, self.tree_snapshot())

    def ok(self, *args, config=None, config_name='config.json'):
        result = self.run_install(*args, config=config, config_name=config_name)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_zero_packs_every_host_lifecycle_and_content(self):
        for host, agent, checkpoint in [
            ('opencode', '.config/opencode/agents/study-lead.md', '.config/opencode/commands/study-lead-checkpoint.md'),
            ('claude', '.claude/agents/study-lead.md', '.claude/skills/study-lead-checkpoint/SKILL.md'),
            ('codex', '.codex/study-lead.config.toml', '.agents/skills/study-lead-checkpoint/SKILL.md'),
            ('pi', '.pi/agent/prompts/study-lead.md', '.pi/agent/skills/study-lead-checkpoint/SKILL.md')]:
            with self.subTest(host=host):
                self.config['hosts'] = [host]
                printed = self.ok('--print')
                self.assertEqual(printed, self.ok('--print'))
                self.assertNotIn(str(self.root / 'config.json'), printed)
                self.ok('--dry-run')
                self.assertFalse(self.snapshot())
                self.assertNotIn('{{', printed)
                for absent in ('a2a', 'openchamber', 'runway', 'tarmac', 'docket', 'fleet', 'chief',
                               'pi-subagents', 'pi-goal-x', 'subagents_enable', 'get_goal', 'create_goal'):
                    self.assertNotIn(absent, printed.lower())
                self.assertIn('work yourself', printed)
                self.assertIn('Do not claim that a new session exists', printed)
                self.ok()
                self.assertEqual(len(self.snapshot()), 3)
                state = next((self.home / '.local/state/lead-kit').glob('*.json'))
                data = json.loads(state.read_text())
                self.assertEqual(data['version'], 2)
                self.assertEqual(data['installation'], state.stem)
                self.assertEqual(data['hosts'], [host])
                self.assertEqual(data['outputs'], [agent, checkpoint])
                text = (self.home / agent).read_text()
                for resource in (agent, checkpoint):
                    path = self.home / resource
                    self.assertIn(f'=== {path}\n{path.read_text()}\n', printed)
                self.assertIn('study-lead-checkpoint', text)
                self.assertIn('agent `study-lead`', (self.home / checkpoint).read_text())
                if host == 'opencode':
                    self.assertIn('mode: primary', text)
                    self.assertNotIn('effect: deny', text)
                    self.assertIn('native `subagent`', text)
                elif host == 'claude':
                    self.assertIn('name: study-lead', text)
                    self.assertIn('claude --agent study-lead', text)
                elif host == 'pi':
                    self.assertTrue(text.startswith('---\ndescription:'))
                    self.assertIn('argument-hint: "[task]"', text)
                    self.assertIn('Operator request: $ARGUMENTS', text)
                    self.assertIn('/study-lead <task>', text)
                    self.assertIn('/skill:study-lead-checkpoint', text)
                    skill = (self.home / checkpoint).read_text()
                    self.assertTrue(skill.startswith('---\nname: study-lead-checkpoint\n'))
                    self.assertIn('/study-lead Read LEAD.md', skill)
                else:
                    try:
                        import tomllib
                    except ImportError:
                        parsed = {'developer_instructions': json.loads(text.split('developer_instructions = ', 1)[1])}
                    else:
                        parsed = tomllib.loads(text)
                    self.assertIn('codex --profile study-lead', parsed['developer_instructions'])
                    self.assertIn('$study-lead-checkpoint', parsed['developer_instructions'])
                before = self.snapshot()
                self.ok()
                self.assertEqual(before, self.snapshot())
                self.ok('--uninstall')
                self.assertFalse(self.snapshot())
                self.ok('--uninstall')

    def test_selected_only_and_deterministic_composition(self):
        packs = render.registry()
        for p in packs:
            selected = [p['id']] + p['requires']
            config = {**self.config, 'practices': selected if p['kind'] == 'practice' else [],
                      'capabilities': selected if p['kind'] == 'capability' else [],
                      'hosts': [p['hosts'][0]]}
            printed = self.ok('--print', config=config)
            for item in packs:
                content = render.read(item['content'])
                # A substantive sentence, not just a pack heading.
                sentence = content.split('\n\n')[1].split('\n')[0]
                if item['id'] in selected:
                    self.assertIn(sentence, printed)
                else:
                    self.assertNotIn(content.splitlines()[0], printed)
            if p['id'] == 'a2a':
                self.assertNotIn('openchamber', printed.lower())
                self.assertNotIn('runway', printed.lower())
            if p['id'] == 'openchamber':
                self.assertNotIn('a2a', printed)
        config = {**self.config, 'practices': ['research', 'engineering'],
                  'capabilities': ['runway', 'a2a', 'openchamber']}
        first = self.ok('--print', config=config)
        config['practices'].reverse()
        config['capabilities'].reverse()
        self.assertEqual(first, self.ok('--print', config=config))
        self.assertLess(first.index('## Capability: OpenChamber'), first.index('## Capability: Runway'))

    def test_all_practices_and_owner_binding(self):
        config = {**self.config, 'practices': ['engineering', 'research', 'life-admin']}
        printed = self.ok('--print', config=config)
        self.assertIn('regression checks', printed)
        self.assertIn('source ledger', printed)
        self.assertIn('time zone', printed)
        owner = dict(mode='agent', integration='openchamber', pointer=str(self.root / 'owner.json'), label='coordinator')
        config = {**config, 'owner': owner, 'capabilities': ['openchamber']}
        printed = self.ok('--print', config=config)
        for text in ('Before every send', '`session` and absolute `directory`', 'returnResult: true',
                     'Never guess, title-search', 'log the blocked delivery and ask'):
            self.assertIn(text, printed)
        self.assertNotEqual(self.run_install(config={**config, 'capabilities': []}).returncode, 0)
        self.assertFalse(self.snapshot())

    def test_invalid_configs_no_writes(self):
        invalid = [{}, {**self.config, 'version': True}, {**self.config, 'hosts': []},
                   {**self.config, 'hosts': ['opencode', 'opencode']},
                   {**self.config, 'hosts': ['other']}, {**self.config, 'extra': 1}]
        for field in ('practices', 'capabilities'):
            invalid += [{**self.config, field: x} for x in ('research', [None], [[]], ['bad'], ['../escape'], ['research', 'research'])]
        invalid += [{**self.config, 'agent': n} for n in ('../escape', 'Lead', 'lead', 'checkpoint', 'shape', 'build')]
        invalid += [{**self.config, 'capabilities': ['runway']},
                    {**self.config, 'capabilities': ['a2a', 'a2a']},
                    {**self.config, 'capabilities': ['openchamber'], 'hosts': ['claude']},
                    {**self.config, 'capabilities': ['a2a'], 'hosts': ['opencode', 'codex']},
                    {**self.config, 'owner': {'mode': 'principal', 'style': '{{HOST}}'}},
                    {**self.config, 'owner': {'mode': 'agent', 'pointer': 'relative', 'label': 'owner'} }]
        for config in invalid:
            with self.subTest(config=config):
                result = self.run_install(config=config)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.snapshot())

    def test_old_config_and_positional_host_migration(self):
        old = dict(version=1, agent='study-lead', packs=['research'], owner=self.config['owner'])
        result = self.run_install(config=old)
        self.assertIn('config v1 migration', result.stderr)
        self.assertFalse(self.snapshot())
        self.assertNotEqual(self.run_install('codex').returncode, 0)

    def test_config_changes_remove_stale_hosts_names_and_capabilities(self):
        self.config.update(hosts=['opencode', 'claude', 'codex'], practices=['engineering'])
        self.ok()
        self.assertEqual(len(self.snapshot()), 7)
        self.config.update(agent='renamed-lead', hosts=['opencode'], capabilities=['a2a'])
        before = self.snapshot()
        preview = self.ok('--print')
        self.assertIn('would remove', preview)
        self.assertEqual(before, self.snapshot())
        self.ok()
        self.assertEqual(len(self.snapshot()), 3)
        self.assertFalse(any('study-lead' in p for p in self.snapshot()))
        self.config['capabilities'] = []
        self.ok()
        self.assertNotIn('a2a', (self.home / '.config/opencode/agents/renamed-lead.md').read_text())
        self.ok('--uninstall')
        self.assertFalse(self.snapshot())

    def test_unrecorded_legacy_outputs_are_not_cleanup_candidates(self):
        old = self.home / '.codex/skills/study-lead-checkpoint/SKILL.md'
        old.parent.mkdir(parents=True)
        old.write_text('<!-- managed by chief-of-staff/install.sh; standalone lead study-lead -->\nlegacy')
        unowned = self.home / '.codex/study-lead.config.toml'
        unowned.write_text('keep')
        self.ok()
        self.assertTrue(old.exists())
        self.assertEqual(unowned.read_text(), 'keep')
        self.ok('--uninstall')
        self.assertTrue(old.exists())
        self.assertEqual(unowned.read_text(), 'keep')

    def test_cross_config_same_host_name_collision_and_missing_outputs(self):
        self.ok()
        self.rejects_without_mutation(config_name='other.json')
        # The registry still reserves paths if files have gone missing.
        for p in (self.home / '.config/opencode').rglob('*.md'):
            p.unlink()
        self.rejects_without_mutation(config_name='other.json')

    def test_disjoint_host_rename_and_uninstall_preserve_other_installation(self):
        self.config['agent'] = 'alpha-lead'
        self.ok()
        other = {**self.config, 'agent': 'beta-lead', 'hosts': ['claude']}
        self.ok(config=other, config_name='other.json')
        other_bytes = {p: b for p, b in self.snapshot().items() if p.startswith('.claude/')}
        other_state = next(p for p in (self.home / '.local/state/lead-kit').glob('*.json')
                           if json.loads(p.read_text())['agent'] == 'beta-lead')
        record_bytes = other_state.read_bytes()
        self.config['agent'] = 'beta-lead'
        before = self.tree_snapshot()
        self.ok('--print')
        self.assertEqual(before, self.tree_snapshot())
        self.ok()
        self.assertEqual(other_bytes, {p: b for p, b in self.snapshot().items() if p.startswith('.claude/')})
        self.assertEqual(record_bytes, other_state.read_bytes())
        for mode in ('--uninstall', None, '--uninstall'):
            self.ok(*([mode] if mode else []))
            self.assertEqual(record_bytes, other_state.read_bytes())
            self.assertEqual(other_bytes, {p: b for p, b in self.snapshot().items() if p.startswith('.claude/')})
        self.ok('--uninstall', config=other, config_name='other.json')
        self.assertFalse(self.snapshot())

    def test_collision_during_host_change_preserves_both_records(self):
        self.ok()
        other = {**self.config, 'hosts': ['claude']}
        self.ok(config=other, config_name='other.json')
        self.rejects_without_mutation(config={**self.config, 'hosts': ['claude']})
        self.ok('--uninstall')
        self.rejects_without_mutation(config={**self.config, 'hosts': ['claude']})
        self.ok('--uninstall', config=other, config_name='other.json')
        self.ok(config={**self.config, 'hosts': ['claude']})

    def test_unselected_host_symlink_is_not_preflighted(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'sentinel').write_bytes(b'keep')
        (self.home / '.claude').symlink_to(outside, target_is_directory=True)
        before = self.tree_snapshot()
        printed = self.ok('--print')
        self.assertEqual(printed, self.ok('--print'))
        self.ok('--dry-run')
        self.assertEqual(before, self.tree_snapshot())
        self.ok()
        self.ok('--uninstall')
        self.assertEqual(b'keep', (outside / 'sentinel').read_bytes())
        self.assertEqual([outside / 'sentinel'], list(outside.iterdir()))
        self.assertEqual(before['.claude'], self.tree_snapshot()['.claude'])

    def test_recorded_old_host_symlink_blocks_all_mutation(self):
        self.config['hosts'] = ['claude']
        self.ok()
        host = self.home / '.claude'
        moved = self.root / 'saved-claude'
        host.rename(moved)
        saved = {str(p.relative_to(moved)): p.read_bytes() for p in moved.rglob('*') if p.is_file()}
        host.symlink_to(moved, target_is_directory=True)
        self.config.update(hosts=['opencode'], agent='renamed-lead')
        self.rejects_without_mutation()
        self.assertEqual(saved, {str(p.relative_to(moved)): p.read_bytes()
                                 for p in moved.rglob('*') if p.is_file()})

    def test_name_only_and_chief_markers_never_authorize_adoption(self):
        target = self.home / '.config/opencode/agents/study-lead.md'
        target.parent.mkdir(parents=True)
        for label in ('managed by lead-kit/install.sh; lead study-lead',
                      'managed by chief-of-staff/install.sh; standalone lead study-lead'):
            target.write_text(f'<!-- {label} -->\nlegacy')
            self.rejects_without_mutation()

    def test_legacy_records_require_explicit_migration(self):
        self.ok()
        state = next((self.home / '.local/state/lead-kit').glob('*.json'))
        state.write_text(json.dumps({'version': 1, 'agent': self.config['agent']}))
        self.rejects_without_mutation()
        self.rejects_without_mutation(config_name='other.json')

    def test_recorded_outputs_require_matching_identity_even_when_stale(self):
        self.ok()
        target = self.home / '.config/opencode/commands/study-lead-checkpoint.md'
        state = next((self.home / '.local/state/lead-kit').glob('*.json'))
        target.write_text(target.read_text().replace(state.stem, '0' * 24))
        self.rejects_without_mutation()
        self.config.update(agent='renamed-lead', hosts=['claude'])
        self.rejects_without_mutation()

    def test_records_cannot_claim_arbitrary_or_unrecorded_paths(self):
        self.ok()
        state = next((self.home / '.local/state/lead-kit').glob('*.json'))
        original = json.loads(state.read_text())
        sentinel = self.home / 'sentinel'
        sentinel.write_bytes(b'keep')
        bad_records = [
            {**original, 'outputs': ['sentinel']},
            {**original, 'outputs': [str(sentinel)]},
            {**original, 'outputs': ['../sentinel']},
            {**original, 'hosts': ['legacy']},
            {**original, 'hosts': ['opencode', 'opencode']},
            {**original, 'installation': '0' * 24},
            {**original, 'agent': '../escape'},
            {**original, 'extra': True},
            {**original, 'version': True},
            {**original, 'outputs': original['outputs'][:1]},
        ]
        for data in bad_records:
            with self.subTest(record=data):
                state.write_text(json.dumps(data))
                self.rejects_without_mutation()
        for text in ('{', '[]', 'null'):
            state.write_text(text)
            self.rejects_without_mutation()
        state.write_text(json.dumps(original))
        # An identity marker without its record is not authority either.
        state.unlink()
        self.rejects_without_mutation()

    def test_other_registry_record_validation_and_symlinks(self):
        self.ok()
        directory = self.home / '.local/state/lead-kit'
        own = next(directory.glob('*.json'))
        other = directory / ('0' * 24 + '.json')
        other.write_text(own.read_text())
        self.rejects_without_mutation()
        other.unlink()
        other.symlink_to(own)
        self.rejects_without_mutation()
        other.unlink()
        other = directory / 'unexpected.json'
        other.write_text(own.read_text())
        self.rejects_without_mutation()

    def test_unowned_last_target_blocks_all_modes(self):
        self.ok()
        last = self.home / '.config/opencode/commands/study-lead-checkpoint.md'
        last.write_text('unowned fixture')
        before = self.snapshot()
        for mode in ((), ('--uninstall',), ('--print',), ('--dry-run',)):
            self.assertNotEqual(self.run_install(*mode).returncode, 0)
            self.assertEqual(before, self.snapshot())

    def test_symlinks_and_nondirectories_rejected(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'sentinel').write_text('keep')
        (self.home / '.config').symlink_to(outside, target_is_directory=True)
        self.rejects_without_mutation()
        for mode in ((), ('--uninstall',), ('--print',), ('--dry-run',)):
            result = self.run_install(*mode)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('symlinked destination', result.stderr)
            self.assertEqual(list(outside.iterdir()), [outside / 'sentinel'])
        (self.home / '.config').unlink()
        self.ok()
        leaf = self.home / '.config/opencode/agents/study-lead.md'
        leaf.unlink()
        leaf.symlink_to(outside / 'sentinel')
        self.rejects_without_mutation()
        self.assertEqual('keep', (outside / 'sentinel').read_text())

    def test_state_symlink_and_corruption_block_changes(self):
        self.ok()
        state = next((self.home / '.local/state/lead-kit').glob('*.json'))
        state.write_text('{"version":1,"agent":"../escape"}')
        before = self.snapshot()
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertEqual(before, self.snapshot())
        state.unlink()
        state.symlink_to(self.root / 'missing')
        self.rejects_without_mutation()

    def test_selected_home_alias_allowed_and_destination_guards(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.home, target_is_directory=True)
        self.env['HOME'] = str(alias)
        self.ok()
        self.assertEqual(len(self.snapshot()), 3)
        self.ok('--uninstall')
        guard = DestinationRoot(self.home)
        (self.home / 'file').write_text('keep')
        for target in (self.root / 'escape', self.home / '../escape', self.home, self.home / 'file/child'):
            with self.assertRaises(ValueError):
                guard.validate_all([target])

    def test_manifest_validation_and_discovery(self):
        original = render.read
        packs = json.loads(original('packs.json'))
        cases = [packs + [packs[0]], [{**packs[0], 'content': '../outside'}],
                 [{**packs[0], 'hosts': ['bad']}], [{**packs[0], 'requires': ['missing']}],
                 [{**packs[0], 'requires': ['engineering']}], [{**packs[0], 'extra': True}]]
        for bad in cases:
            with patch.object(render, 'read', side_effect=lambda p: json.dumps(bad) if p == 'packs.json' else original(p)):
                with self.assertRaises(ValueError):
                    render.registry()
        result = self.cli('--list-packs')
        self.assertEqual(result.returncode, 0, result.stderr)
        listed = result.stdout
        self.assertIn('requires: openchamber', listed)
        for group in ('Practices:', 'OpenCode integrations:', 'Pi extensions:', 'External service integrations:'):
            self.assertIn(group, listed)
        self.assertFalse(self.snapshot())

    def test_unknown_pack_placeholder_fails(self):
        original = render.read
        for token in ('{{MISSING}}', '{{missing}}'):
            with patch.object(render, 'read', side_effect=lambda p: token if p.endswith('instructions.md') else original(p)):
                with self.assertRaisesRegex(ValueError, 'unknown pack placeholder'):
                    render.registry()
        with self.assertRaisesRegex(ValueError, 'malformed'):
            render.expand('{{unfinished', {})

    def test_toml_escaping_and_nonempty_reporting_text(self):
        self.config.update(hosts=['codex'], owner={'mode': 'principal', 'style': 'Use "quotes", apostrophes \'\'\' and \\ paths.'})
        printed = self.ok('--print')
        self.assertIn('apostrophes', printed)
        self.ok()
        text = (self.home / '.codex/study-lead.config.toml').read_text()
        try:
            import tomllib
        except ImportError:
            prompt = json.loads(text.split('developer_instructions = ', 1)[1])
        else:
            prompt = tomllib.loads(text)['developer_instructions']
        self.assertIn(self.config['owner']['style'], prompt)
        self.ok('--uninstall')
        for style in ('', 'line\nbreak', '`code`'):
            self.assertNotEqual(self.run_install(config={**self.config, 'owner': {'mode': 'principal', 'style': style}}).returncode, 0)
        self.assertFalse(self.snapshot())

    def test_pi_capability_matrix_and_preview_agreement(self):
        self.config['hosts'] = ['pi']
        for selected in ([], ['pi-subagents'], ['pi-goal-x'], ['pi-goal-x', 'pi-subagents']):
            with self.subTest(selected=selected):
                self.config['capabilities'] = selected
                printed = self.ok('--print')
                self.ok('--dry-run')
                self.assertFalse(self.snapshot())
                self.ok()
                for path, data in self.snapshot().items():
                    if path.endswith('.md'):
                        self.assertIn(f'=== {self.home / path}\n{data.decode()}\n', printed)
                for pack, token in [('pi-subagents', 'subagents_enable'), ('pi-goal-x', 'get_goal')]:
                    self.assertEqual(token in printed, pack in selected)
                if 'pi-subagents' in selected:
                    for token in ('async: false', 'timeoutMs: 120000', 'action: "status"', 'receipt confirms launch only'):
                        self.assertIn(token, printed)
                if 'pi-goal-x' in selected:
                    for token in ('operator explicitly requests goal mode', 'status: "paused"',
                                  'status: "complete"', 'unset means unlimited', 'strictExecutionContract'):
                        self.assertIn(token, printed)
                for absent in ('openchamber', 'a2a_send', 'returnResult'):
                    self.assertNotIn(absent, printed)
                self.ok('--uninstall')
                self.assertFalse(self.snapshot())

    def test_pi_selection_and_multi_host_rules(self):
        for pack in ('pi-subagents', 'pi-goal-x'):
            for hosts in (['opencode'], ['claude'], ['codex'], ['pi', 'opencode']):
                self.rejects_without_mutation(config={**self.config, 'hosts': hosts, 'capabilities': [pack]})
        for pack in ('a2a', 'openchamber', 'runway'):
            self.rejects_without_mutation(config={**self.config, 'hosts': ['pi'], 'capabilities': [pack]})
        owner = dict(mode='agent', integration='openchamber', pointer='/operator/owner.json', label='owner')
        self.rejects_without_mutation(config={**self.config, 'hosts': ['pi'], 'owner': owner})
        self.config.update(hosts=list(render.HOSTS), practices=['engineering'])
        printed = self.ok('--print')
        self.ok()
        self.assertEqual(len(self.snapshot()), 9)
        self.assertEqual(printed.count('# Project lead'), 4)
        for path, data in self.snapshot().items():
            if path.endswith('.md') and not path.startswith('.pi/'):
                for token in (b'Pi host', b'subagents_enable', b'get_goal', b'pi-goal-x'):
                    self.assertNotIn(token, data)
        self.ok('--uninstall')
        self.assertFalse(self.snapshot())

    def test_pi_same_config_host_changes_and_reservations(self):
        self.ok()
        self.config['hosts'] = ['pi']
        self.assertIn('would remove', self.ok('--print'))
        self.ok()
        self.assertFalse(any(p.startswith('.config/opencode/') for p in self.snapshot()))
        self.rejects_without_mutation(config_name='other.json')
        for path in (self.home / '.pi').rglob('*.md'):
            path.unlink()
        self.rejects_without_mutation(config_name='other.json')
        self.ok()  # Only the owning config can repair missing outputs.
        other = {**self.config, 'hosts': ['claude']}
        self.ok(config=other, config_name='other.json')
        self.rejects_without_mutation(config=other)
        self.ok('--uninstall', config=other, config_name='other.json')
        self.config.update(hosts=['codex'], agent='renamed-lead')
        self.ok()
        self.assertFalse(any(p.startswith('.pi/') for p in self.snapshot()))
        self.ok('--uninstall')
        self.assertFalse(self.snapshot())

    def test_pi_path_guards_and_unselected_symlink(self):
        outside = self.root / 'outside'
        outside.mkdir()
        sentinel = outside / 'sentinel'
        sentinel.write_bytes(b'keep')
        link = self.home / '.pi'
        link.symlink_to(outside, target_is_directory=True)
        self.ok('--print')
        self.ok('--dry-run')
        self.ok()
        self.ok('--uninstall')
        self.config['hosts'] = ['pi']
        self.rejects_without_mutation()
        link.unlink()
        # Cover both resource leaves and their parent directories.
        for relative in ('.pi/agent/prompts', '.pi/agent/skills',
                         '.pi/agent/prompts/study-lead.md',
                         '.pi/agent/skills/study-lead-checkpoint/SKILL.md'):
            path = self.home / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(outside, target_is_directory=True)
            self.rejects_without_mutation()
            path.unlink()
        self.ok()
        old = self.home / '.pi'
        saved = self.root / 'saved-pi'
        old.rename(saved)
        saved_bytes = {str(p.relative_to(saved)): p.read_bytes() for p in saved.rglob('*') if p.is_file()}
        old.symlink_to(saved, target_is_directory=True)
        self.config['hosts'] = ['claude']
        self.rejects_without_mutation()
        self.assertEqual(saved_bytes, {str(p.relative_to(saved)): p.read_bytes() for p in saved.rglob('*') if p.is_file()})
        self.assertEqual(list(outside.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b'keep')

    def test_pi_unowned_and_mismatched_checkpoint_block_all_modes(self):
        self.config['hosts'] = ['pi']
        target = self.home / '.pi/agent/skills/study-lead-checkpoint/SKILL.md'
        target.parent.mkdir(parents=True)
        target.write_text('manual skill')
        self.rejects_without_mutation()
        target.unlink()
        self.ok()
        state = next((self.home / '.local/state/lead-kit').glob('*.json'))
        target.write_text(target.read_text().replace(state.stem, '0' * 24))
        self.rejects_without_mutation()
        self.config.update(hosts=['opencode'], agent='renamed-lead')
        self.rejects_without_mutation()

    def test_presets_preview_install_reinstall_and_uninstall_identity(self):
        keys = set()
        for host in render.HOSTS:
            with self.subTest(host=host):
                config_path = SRC / 'presets' / (host + '.json')
                config = json.loads(config_path.read_text())
                self.assertEqual(config['hosts'], [host])
                self.assertEqual(config['agent'], 'project-lead')
                self.assertEqual(config['capabilities'], [])
                before = self.tree_snapshot()
                preview = self.cli('--preset', host, '--print')
                self.assertEqual(preview.returncode, 0, preview.stderr)
                direct = self.cli('--lead-config', str(config_path), '--print')
                self.assertEqual(direct.returncode, 0, direct.stderr)
                self.assertEqual(preview.stdout, direct.stdout)
                self.assertEqual(self.cli('--preset', host, '--dry-run').returncode, 0)
                self.assertEqual(before, self.tree_snapshot())
                self.assertFalse(list(self.root.glob('*.json')))  # No user-authored config.
                self.assertEqual(self.cli('--preset', host).returncode, 0)
                key = hashlib.sha256(str(config_path.resolve()).encode()).hexdigest()[:24]
                keys.add(key)
                state = self.home / '.local/state/lead-kit' / (key + '.json')
                record = json.loads(state.read_text())
                self.assertEqual(record['hosts'], [host])
                self.assertEqual(record['installation'], key)
                self.assertEqual(len(self.snapshot()), 3)
                for relative in record['outputs']:
                    path = self.home / relative
                    self.assertIn('installation ' + key, path.read_text())
                    self.assertIn(f'=== {path}\n{path.read_text()}\n', preview.stdout)
                installed = self.tree_snapshot()
                for args in (('--print',), ('--dry-run',), ()):
                    result = self.cli('--preset', host, *args)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(installed, self.tree_snapshot())
                self.assertEqual(self.cli('--lead-config', str(config_path), '--uninstall').returncode, 0)
                self.assertFalse(self.snapshot())
                self.assertEqual(self.cli('--preset', host).returncode, 0)
                self.assertEqual(installed, self.tree_snapshot())
                self.assertEqual(self.cli('--preset', host, '--uninstall').returncode, 0)
                self.assertFalse(self.snapshot())
        self.assertEqual(len(keys), 4)

    def test_preset_flag_errors_are_nonmutating(self):
        for args in ((), ('--preset',), ('--lead-config',), ('--preset', '--print'),
                     ('--preset', 'unknown'), ('--preset', 'opencode', '--preset', 'pi'),
                     ('--preset', 'pi', '--lead-config', 'missing.json'),
                     ('--lead-config', 'missing.json', '--preset', 'pi'),
                     ('--lead-config', 'a.json', '--lead-config', 'b.json'),
                     ('--preset', 'opencode', '--print', '--dry-run'),
                     ('--preset', 'opencode', '--uninstall', '--print'),
                     ('--preset', 'pi', '--list-packs'), ('--list-packs', '--print'),
                     ('--list-packs', '--list-packs'), ('pi',)):
            before = self.tree_snapshot()
            result = self.cli(*args)
            self.assertNotEqual(result.returncode, 0, (args, result.stdout))
            self.assertEqual(before, self.tree_snapshot())
        help_text = self.cli('--help')
        self.assertEqual(help_text.returncode, 0)
        self.assertIn('--preset HOST | --lead-config FILE', help_text.stdout)

    def test_preset_custom_copy_cannot_claim_installation(self):
        self.assertEqual(self.cli('--preset', 'opencode').returncode, 0)
        config = json.loads((SRC / 'presets/opencode.json').read_text())
        self.rejects_without_mutation(config=config)
        self.assertEqual(self.cli('--preset', 'opencode', '--uninstall').returncode, 0)
        self.ok(config=config)
        before = self.tree_snapshot()
        self.assertNotEqual(self.cli('--preset', 'opencode').returncode, 0)
        self.assertEqual(before, self.tree_snapshot())
        self.ok('--uninstall', config=config)

    def test_tarmac_selected_only_on_each_host_without_dispatch_dependency(self):
        for host in render.HOSTS:
            self.config.update(hosts=[host], capabilities=[])
            self.assertNotIn('/api/v1/snapshot', self.ok('--print'))
            self.config['capabilities'] = ['tarmac']
            printed = self.ok('--print')
            for token in ('GET /api/v1/snapshot', 'schema_version: 2', 'passive: true',
                          'Reads need no bearer token', 'operator-provided endpoint',
                          'Model-to-bucket applicability', 'Treat missing, stale or unknown',
                          'does not reserve capacity', 'unit', 'fresh_until'):
                self.assertIn(token, printed)
            for absent in ('session.create', 'prepare`', 'a2a_send', 'subagents_enable', 'get_goal'):
                self.assertNotIn(absent, printed)
            self.ok()
            for path, data in self.snapshot().items():
                if path.endswith('.md'):
                    self.assertIn(f'=== {self.home / path}\n{data.decode()}\n', printed)
            self.ok('--uninstall')
            self.assertFalse(self.snapshot())
        pack = next(p for p in render.registry() if p['id'] == 'tarmac')
        self.assertEqual(pack['requires'], [])
        self.assertEqual(pack['hosts'], list(render.HOSTS))
        self.rejects_without_mutation(config={**self.config, 'hosts': ['other']})

    def test_removed_fleet_is_explicit_error_without_cleanup(self):
        self.ok()
        legacy = self.home / 'legacy-fleet-note.md'
        legacy.write_text('unowned fixture; preserve')
        self.config['capabilities'] = ['fleet']
        self.rejects_without_mutation()
        result = self.run_install('--print')
        self.assertIn('capabilities must be a unique list of known IDs', result.stderr)
        self.assertNotIn('fleet', [p['id'] for p in render.registry()])
        self.assertNotIn('fleet', self.cli('--list-packs').stdout)
        self.assertEqual(legacy.read_text(), 'unowned fixture; preserve')

    def test_core_coordinates_resources_and_integration_in_actual_output(self):
        for host in render.HOSTS:
            self.config['hosts'] = [host]
            printed = self.ok('--print')
            for token in ('Take the work request through completion',
                          'allocate a bounded share to each work lane',
                          'Track committed work against the remaining allowance',
                          "operator's stated limits", 'Never invent',
                          'integration order', 'resolve merge',
                          'combined acceptance checks', 'recommended pivot',
                          "Obtain the owner's decision", 'work yourself'):
                self.assertIn(token, printed)

    def test_docket_caller_access_does_not_imply_host_wake_support(self):
        for host in render.HOSTS:
            self.config.update(hosts=[host], capabilities=['docket'])
            printed = self.ok('--print')
            for token in ('https://github.com/batteryshark/docket', 'authorized API access',
                          'targets OpenCode sessions', 'does not give those sessions wake support',
                          'unsupported', 'as blocked'):
                self.assertIn(token, printed)


if __name__ == '__main__':
    unittest.main()
