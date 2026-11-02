import copy
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from .cache import DiskCache
from .repository import ContentRepository, MemoryAdapter, RepoError, REPOSITORY, git_sha
from .tests_repository import SIMPLE


class DiskCacheTests(unittest.TestCase):
    def test_private_atomic_integrity_and_namespace_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = DiskCache(directory, 'a'), DiskCache(directory, 'b')
            self.assertTrue(a.put('item', {'value': '完整内容'}))
            self.assertEqual(a.get('item'), {'value': '完整内容'})
            self.assertIsNone(b.get('item'))
            path = a._path('item')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            data = json.loads(path.read_text())
            data['payload']['value'] = 'tampered'
            path.write_text(json.dumps(data))
            self.assertIsNone(a.get('item'))
            self.assertFalse(path.exists())

    def test_corrupt_schema_key_and_expiry_are_rejected(self):
        for field, replacement in [('schema', 0), ('namespace', 'other'), ('key', 'other'), ('savedAt', -10000000)]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                cache = DiskCache(directory, 'a', clock=lambda: 100.)
                cache.put('item', {'ok': True})
                path = cache._path('item')
                data = json.loads(path.read_text())
                data[field] = replacement
                path.write_text(json.dumps(data))
                self.assertIsNone(cache.get('item'))

    def test_symlink_and_unsafe_permissions_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'link').symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError): DiskCache(root/'link', 'a')
            cache = DiskCache(root, 'a')
            victim = root/'keep.txt'
            victim.write_text('must survive')
            cache._path('item').symlink_to(victim)
            self.assertIsNone(cache.get('item'))
            self.assertEqual(victim.read_text(), 'must survive')
            cache.put('item', {'ok': True})
            cache._path('item').chmod(0o644)
            self.assertIsNone(cache.get('item'))

    def test_interrupted_replace_keeps_old_value(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = DiskCache(directory, 'a')
            cache.put('item', {'old': True})
            with patch('web.server.cache.os.replace', side_effect=OSError('interrupted')):
                self.assertFalse(cache.put('item', {'new': True}))
            self.assertEqual(cache.get('item'), {'old': True})
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_capacity_budget_shared_across_namespaces_and_unrelated_file_survives(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = DiskCache(directory, 'a', max_bytes=1800), DiskCache(directory, 'b', max_bytes=1800)
            keep = Path(directory)/'private-config'
            keep.write_text('keep')
            a.put('one', 'x'*750)
            b.put('two', 'y'*750)
            self.assertLessEqual(sum(p.stat().st_size for p in Path(directory).glob('cache-*.json')), 1800)
            self.assertEqual(keep.read_text(), 'keep')
            self.assertEqual(b.get('two'), 'y'*750)

    def test_catalog_retained_before_source_entries_within_shared_hard_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            notes = DiskCache(directory, 'notes', max_bytes=2400, retained_keys=('catalog',))
            source = DiskCache(directory, 'source', max_bytes=2400)
            notes.put('catalog', 'q' * 700)
            source.put('one', 'a' * 700)
            source.put('two', 'b' * 700)
            self.assertEqual(notes.get('catalog'), 'q' * 700)
            self.assertLessEqual(sum(p.stat().st_size for p in Path(directory).glob('cache-*.json')), 2400)


class CountingAdapter(MemoryAdapter):
    def __init__(self, files=SIMPLE):
        super().__init__(files)
        self.head_calls = self.read_calls = self.tree_calls = 0
        self.block = False
        self.arrived, self.release = threading.Event(), threading.Event()
        self.guard = threading.Lock()
    def head(self):
        with self.guard:
            self.head_calls += 1
        if self.block:
            self.arrived.set()
            if not self.release.wait(5): raise RepoError('github_timeout', 'bounded fixture timeout', 503)
        return super().head()
    def tree(self, revision):
        self.tree_calls += 1
        return super().tree(revision)
    def read(self, revision, path, entry=None):
        self.read_calls += 1
        return super().read(revision, path, entry)


class CatalogCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = [time.time()]
        self.adapter = CountingAdapter()
        self.repo = ContentRepository(self.adapter, cache_root=self.temp.name, cache_ttl=10, clock=lambda: self.now[0])
    def finish(self, repo=None):
        repo = repo or self.repo
        with repo._cache_condition:
            self.assertTrue(repo._cache_condition.wait_for(lambda: not repo._refreshing, 5))
    def test_stale_parallel_reads_are_immediate_and_share_one_refresh(self):
        original = self.repo.catalog()
        self.now[0] += 11
        self.adapter.block = True
        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=20) as pool:
            values = list(pool.map(lambda _: self.repo.catalog(), range(20)))
        self.assertLess(time.monotonic()-started, 1)
        self.assertTrue(self.adapter.arrived.wait(1))
        self.assertEqual(self.adapter.head_calls, 2)
        self.assertTrue(all(v['revision'] == original['revision'] and v['cacheStatus']=='stale' for v in values))
        with ThreadPoolExecutor(max_workers=5) as pool:
            joined = [pool.submit(self.repo.catalog, True) for _ in range(5)]
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                with self.repo._cache_condition:
                    waiting = len(self.repo._cache_condition._waiters)
                if waiting == 5:
                    break
                time.sleep(.005)
            self.assertEqual(waiting, 5)
            self.assertEqual(self.adapter.head_calls, 2)
            self.adapter.release.set()
            for task in joined: self.assertEqual(task.result()['revision'], original['revision'])
        self.finish()
        self.assertEqual(self.adapter.head_calls, 2)
    def test_background_thread_resource_failure_still_returns_success_cache(self):
        original = self.repo.catalog()
        self.now[0] += 11
        with patch('web.server.repository.threading.Thread.start', side_effect=RuntimeError('resource limit')):
            retained = self.repo.catalog()
        self.assertEqual(retained['revision'], original['revision'])
        self.assertTrue(retained['warning'])
        self.assertFalse(retained['refreshing'])

    def test_cold_parallel_requests_join_one_build(self):
        self.adapter.block = True
        with ThreadPoolExecutor(max_workers=10) as pool:
            tasks = [pool.submit(self.repo.catalog) for _ in range(10)]
            self.assertTrue(self.adapter.arrived.wait(1))
            self.assertEqual(self.adapter.head_calls, 1)
            self.adapter.release.set()
            values = [task.result() for task in tasks]
        self.assertTrue(all(value['revision'] == values[0]['revision'] for value in values))
        self.assertEqual(self.adapter.head_calls, 1)

    def test_restart_offline_restores_without_upstream_wait_and_retains_warning(self):
        original = self.repo.catalog()
        self.adapter.fail, self.adapter.block = True, True
        restart = ContentRepository(self.adapter, cache_root=self.temp.name, clock=lambda: self.now[0])
        started = time.monotonic()
        restored = restart.catalog()
        self.assertLess(time.monotonic()-started, .5)
        self.assertEqual(restored['revision'], original['revision'])
        self.assertEqual(restored['cacheStatus'], 'stale')
        self.assertTrue(restored['refreshing'])
        self.adapter.release.set()
        self.finish(restart)
        failed = restart.catalog()
        self.assertTrue(failed['warning'])
        self.assertEqual(failed['revision'], original['revision'])
        calls = self.adapter.head_calls
        for _ in range(10): restart.catalog()
        self.assertEqual(self.adapter.head_calls, calls)
    def test_strict_current_does_not_accept_stale_or_backoff_cache(self):
        original = self.repo.catalog()
        self.adapter.fail = True
        failed = self.repo.catalog(force=True)
        self.assertTrue(failed['warning'])
        with self.assertRaises(RepoError) as caught: self.repo._current(original['revision'])
        self.assertEqual(caught.exception.code, 'github_unavailable')
        self.assertEqual(self.adapter.head_calls, 3)
        self.adapter.fail = False
        self.adapter.atomic_commit(original['revision'], {'README.md':'external change'}, 'external', 'external')
        with self.assertRaises(RepoError) as caught: self.repo._current(original['revision'])
        self.assertEqual(caught.exception.code, 'conflict')
    def test_confirmed_save_updates_cache_and_restart_without_extra_head(self):
        self.repo.catalog()
        editable = self.repo.editable('docs/sample.md#a01')
        draft = self.repo.preview(dict(editable, operation='update', answerMarkdown='缓存必须显示已经确认提交的新回答，同时保留事实边界。'))
        result = self.repo.commit(draft['draftId'], 'cache_commit_0123456789')
        calls = self.adapter.head_calls
        current = self.repo.catalog()
        self.assertEqual(current['revision'], result['commit'])
        self.assertIn('缓存必须显示', current['files'][0]['content'])
        self.assertEqual(self.adapter.head_calls, calls)
        restarted = ContentRepository(self.adapter, cache_root=self.temp.name)
        self.assertEqual(restarted._cache['revision'], result['commit'])
        self.assertIn('缓存必须显示', restarted._cache['files'][0]['content'])
    def test_failed_or_conflicting_save_never_publishes_draft(self):
        self.repo.catalog()
        editable = self.repo.editable('docs/sample.md#a01')
        draft = self.repo.preview(dict(editable, operation='update', answerMarkdown='这份未提交的草稿不能被放进成功缓存里。'))
        original = copy.deepcopy(self.repo._cache)
        self.adapter.fail = True
        with self.assertRaises(RepoError): self.repo.commit(draft['draftId'], 'cache_fail_0123456789')
        self.assertEqual(self.repo._cache, original)
        restarted = ContentRepository(self.adapter, cache_root=self.temp.name)
        self.assertEqual(restarted._cache['revision'], original['revision'])
        self.assertNotIn('未提交的草稿', restarted._cache['files'][0]['content'])
    def test_late_old_refresh_cannot_regress_confirmed_save_memory_or_disk(self):
        original = self.repo.catalog()
        old = copy.deepcopy(self.repo._cache)
        arrived, release = threading.Event(), threading.Event()
        def build_old():
            arrived.set()
            self.assertTrue(release.wait(5))
            return old
        self.now[0] += 11
        with patch.object(self.repo, '_build_catalog', side_effect=build_old):
            self.repo.catalog()
            self.assertTrue(arrived.wait(1))
            changes = {'docs/sample.md': SIMPLE['docs/sample.md'].replace('原始答案足够长', '成功提交的新答案足够长')}
            commit = self.adapter.atomic_commit(original['revision'], changes, 'fixture', 'fixture')
            self.repo._cache_after_commit({'baseRevision':original['revision'], 'changes':changes}, commit)
            release.set()
            self.finish()
        self.assertEqual(self.repo._cache['revision'], commit)
        self.assertEqual(ContentRepository(self.adapter, cache_root=self.temp.name, clock=lambda: self.now[0])._cache['revision'], commit)
    def test_invalid_catalog_integrity_repository_schema_and_corruption_recover_safely(self):
        self.repo.catalog()
        valid = copy.deepcopy(self.repo._cache)
        for mutate in (lambda x: x.update(repository='other/private'), lambda x: x.update(version=99),
                       lambda x: x['files'][0].update(sha='0'*40)):
            value = copy.deepcopy(valid)
            mutate(value)
            self.repo._disk.put('catalog', value)
            restart = ContentRepository(self.adapter, cache_root=self.temp.name)
            self.assertIsNone(restart._cache)
            self.assertEqual(restart.catalog()['revision'], valid['revision'])
        self.repo._disk._path('catalog').write_text('{broken')
        restart = ContentRepository(self.adapter, cache_root=self.temp.name)
        self.assertIsNone(restart._cache)
        self.assertEqual(restart.catalog()['revision'], valid['revision'])
    def test_tree_and_blob_restart_cache_retains_fixed_revision_and_hash_validation(self):
        original = self.repo.catalog()
        restart = ContentRepository(self.adapter, cache_root=self.temp.name)
        self.adapter.tree_calls = self.adapter.read_calls = 0
        self.assertEqual(restart._read(original['revision'], 'docs/sample.md'), SIMPLE['docs/sample.md'])
        self.assertEqual(self.adapter.tree_calls, 0)
        self.assertEqual(self.adapter.read_calls, 0)
        cache = restart._disk
        key = 'blob:docs/sample.md:' + git_sha(SIMPLE['docs/sample.md'])
        cache.put(key, 'tampered but correctly checksummed envelope')
        restart._text_cache.clear()
        self.assertEqual(restart._read(original['revision'], 'docs/sample.md'), SIMPLE['docs/sample.md'])
        self.assertEqual(self.adapter.read_calls, 1)

if __name__ == '__main__': unittest.main()
