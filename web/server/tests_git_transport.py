"""Real local bare-Git transport checks; no GitHub, network or real SSH identities."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from .git_transport import GitSSHAdapter, GitResult, _run_process
from .repository import REPOSITORY, RepoError, git_sha


def git(path, *args, input=None):
    env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
        GIT_AUTHOR_NAME='Local Fixture', GIT_AUTHOR_EMAIL='fixture@localhost.invalid',
        GIT_COMMITTER_NAME='Local Fixture', GIT_COMMITTER_EMAIL='fixture@localhost.invalid')
    result = subprocess.run(['git', '-C', str(path), *args], input=input, capture_output=True, env=env)
    if result.returncode:
        raise AssertionError(result.stderr.decode(errors='replace'))
    return result.stdout.decode().strip()


class GitTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / 'work'; self.work.mkdir()
        git(self.work, 'init', '-b', 'main')
        (self.work / 'docs').mkdir()
        (self.work / 'docs/a.md').write_text('# Fixture\n\n### A01 Example\n\nOriginal bounded answer.\n')
        (self.work / 'docs/keep.md').write_text('Preserved neighbor content.\n')
        git(self.work, 'add', '.')
        git(self.work, 'commit', '-m', 'fixture baseline')
        self.remote = self.root / 'remote.git'
        git(self.root, 'clone', '--bare', str(self.work), str(self.remote))
        git(self.remote, 'config', 'uploadpack.allowFilter', 'true')
        git(self.remote, 'config', 'uploadpack.allowAnySHA1InWant', 'true')
        self.base = git(self.remote, 'rev-parse', 'main')
        self.cache = self.root / 'cache'
        self.calls = []

    def adapter(self, repository=REPOSITORY, allow_write=True, runner=None, metadata_fetcher=None, cache=None):
        def record(argv, **kwargs):
            self.calls.append(argv)
            return _run_process(argv, **kwargs)
        return GitSSHAdapter(repository, cache or self.cache, allow_write=allow_write,
            runner=runner or record, metadata_fetcher=metadata_fetcher or (lambda: {'full_name':repository,'private':False,'default_branch':'main'}),
            _test_remote_resolver=lambda _: str(self.remote))

    def test_real_read_head_tree_utf8_and_no_checkout_or_hooks(self):
        adapter = self.adapter()
        self.assertEqual(adapter.head(), self.base)
        self.assertEqual(adapter.metadata()['defaultBranch'], 'main')
        self.assertFalse(adapter.metadata()['private'])
        tree = adapter.tree(self.base)
        self.assertEqual(tree['docs/a.md']['mode'], '100644')
        original = (self.work / 'docs/a.md').read_text()
        self.assertEqual(adapter.read(self.base, 'docs/a.md', tree['docs/a.md']), original)
        self.assertEqual(tree['docs/a.md']['sha'], git_sha(original))
        commands = [cmd for call in self.calls for cmd in call]
        self.assertIn('core.hooksPath=/dev/null', commands)
        self.assertTrue(all('--git-dir=' in ' '.join(call) or 'init' in call for call in self.calls))
        self.assertTrue(any('BatchMode=yes' in str(value) for value in adapter._env().values()))
        self.assertIn('StrictHostKeyChecking=yes', adapter._env()['GIT_SSH_COMMAND'])

    def test_partial_fetch_does_not_download_all_content_before_selected_read(self):
        adapter = self.adapter()
        tree = adapter.tree(self.base)
        objects = adapter._git(['cat-file', '--batch-all-objects', '--batch-check=%(objectname) %(objecttype)']).stdout
        self.assertNotIn((tree['docs/a.md']['sha']+' blob').encode(), objects)
        self.assertEqual(adapter.read(self.base, 'docs/a.md', tree['docs/a.md']), (self.work/'docs/a.md').read_text())
        objects = adapter._git(['cat-file', '--batch-all-objects', '--batch-check=%(objectname) %(objecttype)']).stdout
        self.assertIn((tree['docs/a.md']['sha']+' blob').encode(), objects)
        self.assertNotIn((tree['docs/keep.md']['sha']+' blob').encode(), objects)

    def test_atomic_multifile_commit_preserves_neighbors_and_idempotency_survives_restart(self):
        adapter = self.adapter()
        changes = {'docs/a.md': '# Changed\n\nNew complete answer.\n', 'docs/new.md': 'A newly created text file.\n'}
        commit = adapter.atomic_commit(self.base, changes, 'fixture edit', 'fixture_transaction_123')
        self.assertEqual(git(self.remote, 'rev-parse', 'main'), commit)
        self.assertEqual(git(self.remote, 'show', commit+':docs/a.md'), changes['docs/a.md'].strip())
        self.assertEqual(git(self.remote, 'show', commit+':docs/keep.md'), 'Preserved neighbor content.')
        self.assertEqual(git(self.remote, 'rev-list', '--count', 'main'), '2')
        self.assertEqual(adapter.atomic_commit(self.base, changes, 'fixture edit', 'fixture_transaction_123'), commit)
        reloaded = self.adapter()
        self.assertEqual(reloaded.atomic_commit(self.base, changes, 'fixture edit', 'fixture_transaction_123'), commit)
        self.assertEqual(git(self.remote, 'rev-list', '--count', 'main'), '2')
        pushes = [x for x in self.calls if 'push' in x]
        self.assertEqual(len(pushes), 1)
        self.assertNotIn('--force', pushes[0]); self.assertNotIn('--force-with-lease', pushes[0])
        with self.assertRaises(RepoError) as error:
            reloaded.atomic_commit(self.base, {'docs/a.md':'Different contents entirely.'}, 'edit', 'fixture_transaction_123')
        self.assertEqual(error.exception.code, 'idempotency_conflict')

    def test_read_only_and_repository_write_scope_fail_before_any_git_activity(self):
        readonly = self.adapter(allow_write=False)
        count = len(self.calls)
        with self.assertRaises(RepoError) as error:
            readonly.atomic_commit(self.base, {'docs/a.md':'Never written.'}, 'edit', 'fixture_read_only_123')
        self.assertEqual(error.exception.code, 'repository_read_only')
        self.assertEqual(len(self.calls), count)
        with self.assertRaises(RepoError): self.adapter('hejulian2004/ssh_mobile', allow_write=True)
        with self.assertRaises(RepoError): self.adapter('attacker/arbitrary', allow_write=False)
        source = self.adapter('hejulian2004/ssh_mobile', allow_write=False)
        self.assertEqual(source.head('main'), self.base)

    def test_conflict_and_out_of_scope_paths_do_not_change_remote(self):
        adapter = self.adapter()
        (self.work / 'docs/a.md').write_text('External concurrent complete answer.\n')
        git(self.work, 'add', '.'); git(self.work, 'commit', '-m', 'other editor')
        git(self.work, 'push', str(self.remote), 'main')
        with self.assertRaises(RepoError) as error:
            adapter.atomic_commit(self.base, {'docs/a.md':'Our complete answer.'}, 'edit', 'fixture_conflict_123')
        self.assertEqual(error.exception.code, 'conflict')
        latest = git(self.remote, 'rev-parse', 'main')
        for path in ('../escape.md', '.github/workflows/run.yml', 'web/server/app.py', 'docs/line\nbreak.md'):
            with self.assertRaises(RepoError) as error:
                adapter.atomic_commit(latest, {path:'Not allowed.'}, 'edit', 'fixture_invalid_path_123')
            self.assertEqual(error.exception.code, 'path_denied')
        self.assertEqual(git(self.remote, 'rev-parse', 'main'), latest)

    def test_uncertain_success_is_verified_on_restart_without_second_push(self):
        state = {'block':False,'pushes':0}
        def runner(argv, **kwargs):
            if 'ls-remote' in argv and state['block']:
                raise RepoError('git_timeout', 'Simulated unavailable verification.', 503)
            result = _run_process(argv, **kwargs)
            if 'push' in argv:
                state['pushes'] += 1; state['block'] = True
                raise RepoError('git_timeout', 'Simulated lost push acknowledgement.', 503)
            return result
        adapter = self.adapter(runner=runner)
        changes = {'docs/a.md':'A valid updated answer in a fixture.\n'}
        with self.assertRaises(RepoError) as error:
            adapter.atomic_commit(self.base, changes, 'edit', 'fixture_uncertain_123')
        self.assertEqual(error.exception.code, 'commit_uncertain')
        self.assertEqual(state['pushes'], 1)
        commit = git(self.remote, 'rev-parse', 'main')
        state['block'] = False
        restarted = self.adapter(runner=runner)
        self.assertEqual(restarted.atomic_commit(self.base, changes, 'edit', 'fixture_uncertain_123'), commit)
        self.assertEqual(state['pushes'], 1)
        self.assertEqual(git(self.remote, 'rev-list', '--count', 'main'), '2')

    def test_remote_push_rejection_never_reports_success_or_uses_other_credentials(self):
        hook = self.remote / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n'); hook.chmod(0o700)
        # Adapter disables local hooks, not remote branch policy. The remote fixture
        # deliberately rejects writes exactly as a protected branch would.
        adapter = self.adapter()
        with self.assertRaises(RepoError) as error:
            adapter.atomic_commit(self.base, {'docs/a.md':'A rejected valid answer.'}, 'edit', 'fixture_reject_123')
        self.assertEqual(error.exception.code, 'github_forbidden')
        self.assertEqual(git(self.remote, 'rev-parse', 'main'), self.base)
        self.assertFalse(adapter._transactions)

    def test_private_unknown_visibility_and_unsafe_read_limits(self):
        private = self.adapter(metadata_fetcher=lambda:None)
        self.assertTrue(private.metadata()['private'])
        self.assertTrue(private.metadata()['visibilityVerified'])
        def unavailable(): raise OSError('private provider error not for clients')
        unknown = self.adapter(metadata_fetcher=unavailable)
        self.assertTrue(unknown.metadata()['private']); self.assertFalse(unknown.metadata()['visibilityVerified'])
        for path in ('../README.md', '/etc/passwd', 'docs/no\tfile.md'):
            with self.assertRaises(RepoError): unknown.read(self.base, path)
        with self.assertRaises(RepoError): unknown.head('--upload-pack=evil')
        with self.assertRaises(RepoError): unknown.tree('main')
        (self.work / 'docs/large.md').write_text('x' * 1_500_001)
        (self.work / 'docs/link.md').symlink_to('a.md')
        git(self.work, 'add', '.'); git(self.work, 'commit', '-m', 'fixture size and link')
        git(self.work, 'push', str(self.remote), 'main')
        revision = git(self.remote, 'rev-parse', 'main')
        with self.assertRaises(RepoError) as error: unknown.read(revision, 'docs/large.md')
        self.assertEqual(error.exception.code, 'file_limit')
        with self.assertRaises(RepoError) as error: unknown.read(revision, 'docs/link.md')
        self.assertEqual(error.exception.code, 'path_denied')

    def test_subprocess_time_and_output_limits_are_bounded(self):
        import sys
        with self.assertRaises(RepoError) as error:
            _run_process([sys.executable, '-c', 'import time; time.sleep(10)'], timeout=.1)
        self.assertEqual(error.exception.code, 'git_timeout')
        with self.assertRaises(RepoError) as error:
            _run_process([sys.executable, '-c', 'print("x"*10000)'], timeout=2, max_output=100)
        self.assertEqual(error.exception.code, 'git_limit')

    def test_cache_metadata_is_private_and_symlinks_are_refused(self):
        adapter = self.adapter()
        self.assertEqual(self.cache.stat().st_mode & 0o777, 0o700)
        self.assertEqual(adapter.path.stat().st_mode & 0o777, 0o700)
        other = self.root / 'other'; other.mkdir(mode=0o700)
        link = self.root / 'link'; link.symlink_to(other)
        with self.assertRaises(RepoError): self.adapter(cache=link)
        state = adapter.path / 'study-transactions.json'
        state.symlink_to(self.root / 'missing-secret')
        with self.assertRaises(RepoError): self.adapter()


if __name__ == '__main__': unittest.main()
