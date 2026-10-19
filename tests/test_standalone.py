"""Offline fixtures: isolated homes under this checkout; no harness activation."""
import json
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

    def run_install(self, *args, config=None):
        file = self.root / 'config.json'
        file.write_text(json.dumps(self.config if config is None else config))
        return subprocess.run(['bash', str(SRC / 'install.sh'), '--lead-config', str(file), *args],
                              env=self.env, capture_output=True, text=True, timeout=15)

    def snapshot(self):
        return {str(p.relative_to(self.home)): p.read_bytes() for p in self.home.rglob('*') if p.is_file()}

    def ok(self, *args, config=None):
        result = self.run_install(*args, config=config)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_zero_packs_every_host_lifecycle_and_content(self):
        for host, agent, checkpoint in [
            ('opencode', '.config/opencode/agents/study-lead.md', '.config/opencode/commands/study-lead-checkpoint.md'),
            ('claude', '.claude/agents/study-lead.md', '.claude/skills/study-lead-checkpoint/SKILL.md'),
            ('codex', '.codex/study-lead.config.toml', '.agents/skills/study-lead-checkpoint/SKILL.md')]:
            with self.subTest(host=host):
                self.config['hosts'] = [host]
                printed = self.ok('--print')
                self.assertEqual(printed, self.ok('--print'))
                self.ok('--dry-run')
                self.assertFalse(self.snapshot())
                self.assertNotIn('{{', printed)
                for absent in ('a2a', 'openchamber', 'runway', 'tarmac', 'docket', 'fleet', 'chief'):
                    self.assertNotIn(absent, printed.lower())
                self.assertIn('work yourself', printed)
                self.assertIn('Do not claim that a new session exists', printed)
                self.ok()
                self.assertEqual(len(self.snapshot()), 3)
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
                      'capabilities': selected if p['kind'] == 'capability' else []}
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

    def test_legacy_owned_outputs_migrate_and_unowned_stale_survives(self):
        old = self.home / '.codex/skills/study-lead-checkpoint/SKILL.md'
        old.parent.mkdir(parents=True)
        old.write_text('<!-- managed by chief-of-staff/install.sh; standalone lead study-lead -->\nlegacy')
        unowned = self.home / '.codex/study-lead.config.toml'
        unowned.write_text('keep')
        self.ok()
        self.assertFalse(old.exists())
        self.assertEqual(unowned.read_text(), 'keep')
        self.ok('--uninstall')
        self.assertEqual(unowned.read_text(), 'keep')

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
        self.assertNotEqual(self.run_install().returncode, 0)

    def test_state_symlink_and_corruption_block_changes(self):
        self.ok()
        state = next((self.home / '.local/state/lead-kit').glob('*.json'))
        state.write_text('{"version":1,"agent":"../escape"}')
        before = self.snapshot()
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertEqual(before, self.snapshot())
        state.unlink()
        state.symlink_to(self.root / 'missing')
        self.assertNotEqual(self.run_install().returncode, 0)

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
        listed = self.ok('--list-packs')
        self.assertIn('requires: openchamber', listed)
        self.assertFalse(self.snapshot())

    def test_unknown_pack_placeholder_fails(self):
        original = render.read
        with patch.object(render, 'read', side_effect=lambda p: '{{MISSING}}' if p.endswith('instructions.md') else original(p)):
            with self.assertRaisesRegex(ValueError, 'unknown pack placeholder'):
                render.registry()

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


if __name__ == '__main__':
    unittest.main()
