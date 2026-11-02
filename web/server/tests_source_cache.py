"""Persistent source cache and authorization boundary regressions (no real APIs)."""
import copy
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from .cache import DiskCache
from .repository import ContentRepository, MemoryAdapter, RepoError, REPOSITORY
from .sources import SourceRegistry, RepositoryWithSources
from .tests_sources import MockSourceAdapter, PROJECT, OTHER, SIMPLE_NOTES


class SourceCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'content-cache'
        self.now = [100.0]
        self.source = MockSourceAdapter(PROJECT, private=True)
        self.notes = ContentRepository(MemoryAdapter(SIMPLE_NOTES))
        self.registry = self.make()

    def tearDown(self):
        self.wait(self.registry)
        self.tmp.cleanup()

    def make(self, repositories=(PROJECT,), adapters=None):
        return SourceRegistry(self.notes, lambda: 'unused', repositories=repositories,
            adapters=adapters or {PROJECT: self.source}, clock=lambda: self.now[0],
            provider_version=lambda: 'provider-1', cache_root=self.root)

    @staticmethod
    def wait(registry):
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            with registry._lock:
                pending = list(registry._refreshing.values())
                prewarming = getattr(registry, '_prewarming', False)
            if not pending and not prewarming:
                return
            if pending:
                pending[0].wait(.05)
            else:
                threading.Event().wait(.01)
        raise AssertionError('background worker did not finish')

    def warm(self):
        value = self.registry.read_source('lib/main.dart', repository=PROJECT)
        self.registry.search_source('source', repository=PROJECT)
        return value

    def test_restart_restores_content_index_but_never_model_grants(self):
        value = self.warm()
        self.registry.authorize_source(PROJECT, True, value['revision'], 'provider-1', ['lib/'])
        self.assertTrue(self.registry._grants)
        self.source.calls.clear()
        self.source.denied = True
        restored = self.make()
        item = restored.source_repos()['repositories'][0]
        self.assertTrue(item['available'])
        self.assertFalse(item['allowModelExport'])
        self.assertIsNone(item['authorization'])
        self.assertEqual(restored.read_source('lib/main.dart', repository=PROJECT)['content'], value['content'])
        self.assertEqual(len(restored.search_source('source', repository=PROJECT)['results']), 2)
        self.assertFalse(self.source.calls)
        with self.assertRaises(RepoError):
            restored.read_source('lib/main.dart', repository=PROJECT, path_prefixes=['lib/'])
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)
        for path in self.root.iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            body = path.read_text()
            self.assertNotIn('provider-1', body)
            self.assertNotIn('pathPrefixes', body)

    def test_disabled_repository_never_restores_cached_private_source(self):
        self.warm()
        other = MockSourceAdapter(OTHER)
        restored = self.make((OTHER,), {OTHER: other})
        self.assertNotIn(PROJECT, restored._snapshots)
        with self.assertRaises(RepoError):
            restored.read_source('lib/main.dart', repository=PROJECT)
        self.assertFalse(other.calls)

    def test_cold_listing_is_immediate_and_prewarming_is_progressive(self):
        entered, release = threading.Event(), threading.Event()
        original = self.source.metadata
        def delayed():
            entered.set()
            self.assertTrue(release.wait(3))
            return original()
        self.source.metadata = delayed
        other = MockSourceAdapter(OTHER)
        registry = self.make((PROJECT, OTHER), {PROJECT: self.source, OTHER: other})
        start = time.monotonic()
        value = registry.source_repos()
        self.assertLess(time.monotonic() - start, .25)
        self.assertTrue(entered.wait(1))
        self.assertTrue(value['repositories'][0]['pending'])
        self.assertFalse(other.calls)
        # A selected repository can load independently of another cold clone.
        self.assertEqual(registry.read_source('lib/main.dart', repository=OTHER)['repository'], OTHER)
        release.set()
        self.wait(registry)
        self.assertTrue(all(v['available'] for v in registry.source_repos()['repositories']))

    def test_stale_cache_twenty_callers_singleflight_and_new_commit_revokes_grant(self):
        old = self.warm()
        self.registry.authorize_source(PROJECT, True, old['revision'], 'provider-1', ['lib/'])
        self.source._files['lib/main.dart'] = '// newer source implementation\n'
        self.source._save()
        self.now[0] += 121
        entered, release = threading.Event(), threading.Event()
        original = self.source.metadata
        def delayed():
            entered.set()
            self.assertTrue(release.wait(3))
            return original()
        self.source.metadata = delayed
        self.source.calls.clear()
        start = time.monotonic()
        with ThreadPoolExecutor(max_workers=20) as pool:
            values = list(pool.map(lambda _: self.registry.source_repos(), range(20)))
        self.assertLess(time.monotonic() - start, .5)
        self.assertTrue(entered.wait(1))
        self.assertTrue(all(v['repositories'][0]['revision'] == old['revision'] for v in values))
        self.assertTrue(all(v['repositories'][0]['cacheStatus'] == 'stale' for v in values))
        release.set()
        self.wait(self.registry)
        self.assertEqual(len([c for c in self.source.calls if c[0] == 'metadata']), 1)
        new = self.registry.source_repos()['repositories'][0]
        self.assertNotEqual(new['revision'], old['revision'])
        self.assertFalse(new['allowModelExport'])

    def test_failed_refresh_retains_fixed_cache_with_backoff_but_new_grant_fails(self):
        old = self.warm()
        self.now[0] += 121
        self.source.denied = True
        self.registry.source_repos()
        self.wait(self.registry)
        before = len(self.source.calls)
        for _ in range(5):
            item = self.registry.source_repos()['repositories'][0]
            self.assertEqual(item['cacheStatus'], 'stale')
            self.assertEqual(self.registry.read_source('lib/main.dart', repository=PROJECT)['revision'], old['revision'])
        self.assertEqual(len(self.source.calls), before)
        with self.assertRaises(RepoError):
            self.registry.authorize_source(PROJECT, True, old['revision'], 'provider-1', ['lib/'])
        self.assertFalse(self.registry._grants)

    def test_concurrent_cold_reads_share_snapshot_and_blob_fetch(self):
        entered, release = threading.Event(), threading.Event()
        original = self.source.read
        def delayed(*args):
            entered.set()
            self.assertTrue(release.wait(3))
            return original(*args)
        self.source.read = delayed
        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = [pool.submit(self.registry.read_source, 'lib/main.dart', repository=PROJECT) for _ in range(12)]
            self.assertTrue(entered.wait(1))
            release.set()
            results = [f.result(timeout=3) for f in futures]
        self.assertEqual(len({v['revision'] for v in results}), 1)
        self.assertEqual(len([c for c in self.source.calls if c[0] == 'metadata']), 1)
        self.assertEqual(len([c for c in self.source.calls if c[0] == 'read']), 1)

    def test_wrong_blob_and_poisoned_search_index_are_never_used(self):
        value = self.warm()
        snapshot = self.registry._snapshots[PROJECT]
        key = self.registry._blob_key(snapshot, 'lib/main.dart')
        self.registry._disk.put('text:' + key, {'repository': PROJECT, 'revision': value['revision'],
            'path': 'lib/main.dart', 'sha': snapshot['tree']['lib/main.dart']['sha'], 'content': 'wrong bytes'})
        self.registry._disk.put('index:' + key, {'key': key, 'folded': 'poisoned match'})
        self.source.calls.clear()
        restored = self.make()
        self.assertEqual(restored.search_source('poisoned', repository=PROJECT)['results'], [])
        self.assertEqual(len(restored.search_source('source', repository=PROJECT)['results']), 2)
        self.assertEqual(len([c for c in self.source.calls if c[0] == 'read']), 1)

    def test_snapshot_wrong_commit_schema_or_scope_are_rejected(self):
        self.warm()
        snapshot = self.registry._snapshots[PROJECT]
        for change in ({'repository': OTHER}, {'revision': 'main'}, {'allowedPathPrefixes': ['']},
                       {'private': False, 'visibilityVerified': False}, {'checkedAt': self.now[0] + 500}, {'checkedAt': 10**500}):
            self.registry._disk.put('snapshot:' + PROJECT, snapshot | change)
            restored = self.make()
            self.assertFalse(restored._snapshots)
        self.registry._disk.put('snapshot:' + PROJECT, snapshot)
        cache_path = self.registry._disk._path('snapshot:' + PROJECT)
        cache_path.write_text('{broken')
        self.assertFalse(self.make()._snapshots)

    def test_successful_commit_invalidation_fences_old_background_disk_result(self):
        old = self.warm()
        self.now[0] += 121
        self.source._files['lib/main.dart'] = '// intermediate revision\n'
        self.source._save()
        intermediate = self.source.head()
        entered, release = threading.Event(), threading.Event()
        original = self.source.tree
        def delayed(revision):
            result = original(revision)
            if revision == intermediate:
                entered.set()
                self.assertTrue(release.wait(3))
            return result
        self.source.tree = delayed
        self.registry.source_repos()
        self.assertTrue(entered.wait(1))
        self.source._files['lib/main.dart'] = '// confirmed final commit\n'
        self.source._save()
        confirmed = self.source.head()
        self.registry.invalidate(PROJECT, confirmed)
        release.set()
        self.wait(self.registry)
        self.assertIsNone(self.registry._disk.get('snapshot:' + PROJECT))
        self.assertFalse(self.make()._snapshots)
        self.assertEqual(self.registry.read_source('lib/main.dart', repository=PROJECT)['revision'], confirmed)
        self.assertNotEqual(confirmed, old['revision'])

    def test_wrapper_editable_forwards_explicit_fresh_conflict_reload(self):
        self.notes = ContentRepository(MemoryAdapter(SIMPLE_NOTES), cache_root=self.root)
        wrapper = RepositoryWithSources(self.notes, self.registry)
        wrapper.catalog()
        self.notes.adapter.fail = True
        self.assertEqual(wrapper.editable('docs/sample.md#a01')['number'], 'A01')
        with self.assertRaises(RepoError):
            wrapper.editable('docs/sample.md#a01', fresh=True)

    def test_blob_failure_has_bounded_retry_backoff_and_no_partial_cache(self):
        original = self.source.read
        attempts = []
        def unavailable(*args):
            attempts.append(args)
            raise RepoError('source_unavailable', 'simulated private transport failure', 503)
        self.source.read = unavailable
        for _ in range(5):
            with self.assertRaises(RepoError):
                self.registry.read_source('lib/main.dart', repository=PROJECT)
        self.assertEqual(len(attempts), 1)
        self.assertFalse(self.registry._texts)
        self.source.read = original
        self.now[0] += 6
        self.assertIn('source', self.registry.read_source('lib/main.dart', repository=PROJECT)['content'])
        self.assertFalse(self.registry._text_failures)

    def test_cached_read_and_index_search_recheck_export_revocation(self):
        old = self.warm()
        for method in ('read', 'search'):
            with self.subTest(method=method):
                self.registry.authorize_source(PROJECT, True, old['revision'], 'provider-1', ['lib/'])
                entered, release = threading.Event(), threading.Event()
                attr = '_read' if method == 'read' else '_index'
                original = getattr(self.registry, attr)
                def delayed(*args):
                    value = original(*args)
                    entered.set()
                    self.assertTrue(release.wait(3))
                    return value
                setattr(self.registry, attr, delayed)
                with ThreadPoolExecutor(max_workers=1) as pool:
                    if method == 'read':
                        pending = pool.submit(self.registry.read_source, 'lib/main.dart', repository=PROJECT,
                            revision=old['revision'], path_prefixes=['lib/'])
                    else:
                        pending = pool.submit(self.registry.search_source, 'source', repository=PROJECT,
                            revision=old['revision'], path_prefixes=['lib/'])
                    self.assertTrue(entered.wait(1))
                    self.registry.authorize_source(PROJECT, False)
                    release.set()
                    with self.assertRaises(RepoError) as error:
                        pending.result(timeout=3)
                    self.assertEqual(error.exception.code, 'source_consent')
                setattr(self.registry, attr, original)

    def test_refresh_thread_start_failure_never_strands_cached_read(self):
        old = self.warm()
        self.now[0] += 121
        with patch('web.server.sources.threading.Thread.start', side_effect=RuntimeError('no threads')):
            item = self.registry.source_repos()['repositories'][0]
            self.assertTrue(item['available'])
            self.assertEqual(item['cacheStatus'], 'stale')
            self.assertFalse(self.registry._refreshing)
            self.assertEqual(self.registry.read_source('lib/main.dart', repository=PROJECT)['revision'], old['revision'])
        self.now[0] += 6
        self.registry.source_repos()
        self.wait(self.registry)
        self.assertFalse(self.registry._failures)

    def test_prewarm_thread_start_failure_resets_flag_and_retries_later(self):
        with patch('web.server.sources.threading.Thread.start', side_effect=RuntimeError('no threads')):
            item = self.registry.source_repos()['repositories'][0]
            self.assertTrue(item['pending'])
            self.assertFalse(self.registry._prewarming)
        self.now[0] += 6
        self.registry.source_repos()
        self.wait(self.registry)
        self.assertTrue(self.registry.source_repos()['repositories'][0]['available'])

    def test_notes_wrapper_invalidates_source_only_after_confirmed_write(self):
        source = MockSourceAdapter(REPOSITORY, SIMPLE_NOTES)
        registry = self.make((REPOSITORY,), {REPOSITORY: source})
        registry.read_source('docs/sample.md', repository=REPOSITORY)
        wrapper = RepositoryWithSources(self.notes, registry)
        edit = wrapper.editable('docs/sample.md#a01')
        draft = wrapper.preview(dict(edit, operation='update', answerMarkdown='A confirmed revised answer with original evidence boundary preserved.'))
        self.notes.adapter.fail = True
        with self.assertRaises(RepoError):
            wrapper.commit(draft['draftId'], 'cache_note_commit_12345')
        self.assertIn(REPOSITORY, registry._snapshots)
        self.notes.adapter.fail = False
        wrapper.commit(draft['draftId'], 'cache_note_commit_12345')
        self.assertNotIn(REPOSITORY, registry._snapshots)
        self.assertIsNone(registry._disk.get('snapshot:' + REPOSITORY))

if __name__ == '__main__': unittest.main()
