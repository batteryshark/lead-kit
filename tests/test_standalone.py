"""Offline fixtures: owned scratch only; no host/app/network is invoked."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SRC = Path(__file__).resolve().parent.parent


class StandaloneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.home = self.root / 'home'
        self.home.mkdir()
        self.env = {'PATH': os.environ['PATH'], 'HOME': str(self.home),
                    'TMPDIR': str(self.root), 'XDG_CONFIG_HOME': str(self.home / '.config'),
                    'XDG_DATA_HOME': str(self.home / '.local/share'),
                    'XDG_CACHE_HOME': str(self.home / '.cache'),
                    'PYTHONDONTWRITEBYTECODE': '1'}
        self.config = dict(version=1, agent='study-lead', packs=['research'],
                           owner=dict(mode='principal', style='Short outcomes.'))

    def run_install(self, *args, config=None):
        file = self.root / 'config.json'
        file.write_text(json.dumps(self.config if config is None else config))
        return subprocess.run(['bash', str(SRC / 'install.sh'), '--lead-config', str(file), *args],
                              env=self.env, capture_output=True, text=True, timeout=15)

    def snapshot(self):
        return {str(p.relative_to(self.home)): p.read_bytes() for p in self.home.rglob('*') if p.is_file()}

    def test_three_host_install_render_reinstall_uninstall(self):
        for host, agent, checkpoint in [
            ('opencode', '.config/opencode/agents/study-lead.md', '.config/opencode/commands/study-lead-checkpoint.md'),
            ('claude', '.claude/agents/study-lead.md', '.claude/skills/study-lead-checkpoint/SKILL.md'),
            ('codex', '.codex/study-lead.config.toml', '.codex/skills/study-lead-checkpoint/SKILL.md')]:
            with self.subTest(host=host):
                printed = self.run_install('--print', host)
                self.assertEqual(printed.returncode, 0, printed.stderr)
                self.assertFalse(self.snapshot())
                self.assertNotIn('{{', printed.stdout)
                self.assertNotIn('You run in goal mode', printed.stdout)
                result = self.run_install(host)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(len(self.snapshot()), 2)
                self.assertIn('study-lead-checkpoint', (self.home / agent).read_text())
                self.assertIn('agent `study-lead`', (self.home / checkpoint).read_text())
                before = self.snapshot()
                self.assertEqual(self.run_install(host).returncode, 0)
                self.assertEqual(before, self.snapshot())
                self.assertEqual(self.run_install('--uninstall', host).returncode, 0)
                self.assertFalse(self.snapshot())
                self.assertFalse((self.home / '.chief-of-staff').exists())

    def test_owner_modes_all_packs_and_no_chief_resources(self):
        for owner in (self.config['owner'], dict(mode='agent', pointer=str(self.root / 'owner.json'), label='coordinator')):
            for packs in (['engineering'], ['research'], ['life-admin'], ['engineering', 'research', 'life-admin']):
                result = self.run_install('--print', config={**self.config, 'owner': owner, 'packs': packs})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn('{{', result.stdout)
                self.assertIn('never guess, title-search', result.stdout)
                if owner['mode'] == 'agent':
                    self.assertIn('every send', result.stdout)
                    self.assertIn('`session` and `directory`', result.stdout)
                if 'engineering' in packs:
                    self.assertIn('Sessions stay', result.stdout)
        for name in ('kits/chief', 'profiles', 'hosts', 'routing', 'runway'):
            self.assertFalse((SRC / name).exists())

    def test_invalid_config_and_reserved_names_fail_before_writes(self):
        for config in ({}, {**self.config, 'version': True}, {**self.config, 'packs': []},
                       {**self.config, 'packs': ['research', 'research']},
                       {**self.config, 'owner': dict(mode='agent', pointer='relative', label='owner')},
                       *({**self.config, 'agent': n} for n in ['../escape', 'Lead', 'lead', 'checkpoint', 'shape', 'chief-of-staff'])):
            result = self.run_install(config=config)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(self.snapshot())

    def test_last_unowned_target_blocks_all_writes_and_uninstall(self):
        self.assertEqual(self.run_install().returncode, 0)
        last = self.home / '.codex/skills/study-lead-checkpoint/SKILL.md'
        last.write_text('unowned fixture')
        before = self.snapshot()
        for mode in ((), ('--uninstall',), ('--print',), ('--dry-run',)):
            self.assertNotEqual(self.run_install(*mode).returncode, 0)
            self.assertEqual(before, self.snapshot())

    def test_symlink_ancestors_rejected_all_modes(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'sentinel').write_text('keep')
        linked = self.home / '.codex'
        linked.symlink_to(outside, target_is_directory=True)
        for mode in ((), ('--uninstall',), ('--print',), ('--dry-run',)):
            result = self.run_install(*mode)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('symlinked destination', result.stderr)
            self.assertEqual(list(outside.iterdir()), [outside / 'sentinel'])
            self.assertFalse((self.home / '.config').exists())

    def test_selected_home_alias_allowed(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.home, target_is_directory=True)
        self.env['HOME'] = str(alias)
        self.assertEqual(self.run_install().returncode, 0)
        self.assertEqual(len(self.snapshot()), 6)
        self.assertEqual(self.run_install('--uninstall').returncode, 0)

    def test_destination_guard_escapes_and_nondirectory(self):
        spec = importlib.util.spec_from_file_location('guard', SRC / 'scripts/install_paths.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        guard = module.DestinationRoot(self.home)
        (self.home / 'file').write_text('keep')
        for target in (self.root / 'escape', self.home / '../escape', self.home, self.home / 'file/child'):
            with self.assertRaises(ValueError):
                guard.validate_all([target])


if __name__ == '__main__':
    unittest.main()
