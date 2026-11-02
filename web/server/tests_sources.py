import copy
import json
import unittest
import threading
from concurrent.futures import ThreadPoolExecutor
from .repository import ContentRepository, MemoryAdapter, RepoError, REPOSITORY
from .sources import SourceRegistry, RepositoryWithSources, ReadOnlyGitHubAdapter, AUTHORIZED_REPOSITORIES

PROJECT = 'hejulian2004/ssh_mobile'
OTHER = 'hejulian2004/testDemo'
SIMPLE_NOTES = {'docs/sample.md':'# Notes\n\n### A01 Question\n\nThis is an original study answer with a clear boundary.\n'}

class MockSourceAdapter(MemoryAdapter):
    def __init__(self, repository, files=None, private=False, default_branch='develop'):
        self.repository = repository
        self.private = private
        self.default_branch = default_branch
        self.calls = []
        self.denied = False
        self.link_paths = set()
        super().__init__(files or {'lib/main.dart':'void main() { print("source"); }\n', 'README.md':'# Current source\n'})
    def metadata(self):
        self.calls.append(('metadata',))
        if self.denied:
            raise RepoError('source_unavailable', 'simulated token value must never appear in response', 403)
        return {'repository': self.repository, 'private': self.private, 'defaultBranch': self.default_branch}
    def head(self, default_branch=None):
        if default_branch is not None:
            self.calls.append(('head', default_branch))
            if default_branch != self.default_branch:
                raise AssertionError('registry must use actual default branch')
        return super().head()
    def tree(self, revision):
        self.calls.append(('tree', revision))
        tree = super().tree(revision)
        for path in self.link_paths:
            if path in tree:
                tree[path]['mode'] = '120000'
        return tree
    def read(self, revision, path, entry=None):
        self.calls.append(('read', revision, path))
        return super().read(revision, path, entry)

class SourceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.notes_adapter = MemoryAdapter(SIMPLE_NOTES)
        self.notes = ContentRepository(self.notes_adapter)
        self.source = MockSourceAdapter(PROJECT, private=True)
        self.now = [100.0]
        self.provider = ['provider-1']
        self.registry = SourceRegistry(self.notes, lambda: 'unused-test-only', repositories=(PROJECT,),
            adapters={PROJECT:self.source}, clock=lambda:self.now[0], provider_version=lambda:self.provider[0])

    def grant(self, prefixes=None):
        item = self.registry.source_repos()['repositories'][0]
        return self.registry.authorize_source(PROJECT, True, revision=item['revision'],
            provider_config_version=self.provider[0], path_prefixes=prefixes or ['lib/'])

    def test_registry_exact_names_no_extra_repo_or_write_adapter(self):
        self.assertEqual(len(AUTHORIZED_REPOSITORIES), 4)
        with self.assertRaises(RepoError):
            SourceRegistry(self.notes, lambda:'unused', repositories=('someone/unapproved',))
        with self.assertRaises(RepoError):
            self.registry.read_source('lib/main.dart', repository=OTHER)
        self.assertFalse(self.source.calls)
        adapter = ReadOnlyGitHubAdapter(lambda:'unused', PROJECT)
        self.assertFalse(hasattr(adapter, 'atomic_commit'))
        with self.assertRaises(RepoError):
            ReadOnlyGitHubAdapter(lambda:'unused','someone/unapproved')

    def test_metadata_uses_actual_private_and_default_branch_without_export_default(self):
        item = self.registry.source_repos()['repositories'][0]
        self.assertTrue(item['available'])
        self.assertIs(item['private'], True)
        self.assertEqual(item['defaultBranch'], 'develop')
        self.assertEqual(item['revision'], self.source.head())
        self.assertIn(('head','develop'), self.source.calls)
        self.assertFalse(item['allowModelExport'])
        self.assertIsNone(item['authorization'])
        self.assertEqual(item['allowedPathPrefixes'], ['README.md','lib/'])
        self.assertIn('历史', item['versionNote'])

    def test_metadata_permission_failure_is_per_repo_and_does_not_expose_message(self):
        available = MockSourceAdapter(OTHER, private=False)
        self.source.denied = True
        registry = SourceRegistry(self.notes, lambda:'unused', repositories=(PROJECT,OTHER),
            adapters={PROJECT:self.source,OTHER:available})
        values = registry.source_repos()['repositories']
        self.assertFalse(values[0]['available'])
        self.assertIsNone(values[0]['private'])
        self.assertFalse(values[0]['allowModelExport'])
        self.assertTrue(values[1]['available'])
        self.assertNotIn('token value', json.dumps(values))
        wrapper = RepositoryWithSources(self.notes, registry)
        self.assertEqual(wrapper.catalog()['revision'], self.notes_adapter.head())
        edit = wrapper.editable('docs/sample.md#a01')
        draft = wrapper.preview(dict(edit,operation='update',answerMarkdown='Changed study answer still has its clear context boundary.'))
        wrapper.commit(draft['draftId'],'notes_write_0123456789')
        self.assertEqual(len(self.notes_adapter.commits),1)
        self.assertEqual(len(self.source.commits),0)

    def test_read_result_is_fixed_commit_with_lines_and_no_source_write(self):
        meta = self.registry.source_repos()['repositories'][0]
        value = self.registry.read_source('lib/main.dart', 1, 1, repository=PROJECT, revision=meta['revision'])
        self.assertTrue(value['private'])
        self.assertEqual(value['revision'],meta['revision'])
        self.assertIn(meta['revision'],value['sourceUrl'])
        self.assertTrue(value['sourceUrl'].endswith('#L1-L1'))
        self.assertFalse(value['allowModelExport'])
        self.assertFalse(self.source.commits)
        with self.assertRaises(RepoError):
            self.registry.read_source('lib/main.dart',repository=PROJECT,revision='a'*40)
        with self.assertRaises(RepoError):
            self.registry.read_source('lib/main.dart',repository=PROJECT,revision='main')

    def test_scope_path_checks_exclude_secrets_binaries_dotfiles_and_symlinks(self):
        extras = {
            'lib/credentials.json':'{"secret":"not readable"}', 'lib/.env':'hidden', 'lib/file.pem':'private key',
            'lib/image.png':'binary', 'lib/link.dart':'../../etc/passwd', 'lib/node_modules/pkg/x.js':'not source',
            'lib-secret/hidden.dart':'not in lib prefix', 'native/keys.json':'not registered root',
        }
        self.source._files.update(extras)
        self.source.link_paths.add('lib/link.dart')
        self.source._save()
        for path in extras:
            with self.assertRaises(RepoError, msg=path):
                self.registry.read_source(path,repository=PROJECT)
        for path in ('../etc/passwd','/etc/passwd','lib/../credentials.json','lib\\main.dart'):
            with self.assertRaises(RepoError, msg=path):
                self.registry.read_source(path,repository=PROJECT)
        read_paths = [call[2] for call in self.source.calls if call[0]=='read']
        self.assertFalse(read_paths)

    def test_grant_binds_revision_provider_and_prefix_then_revoke(self):
        metadata = self.grant()['repositories'][0]
        grant = metadata['authorization']
        self.assertTrue(metadata['allowModelExport'])
        self.assertEqual(grant['providerConfigVersion'],'provider-1')
        self.assertEqual(grant['pathPrefixes'],['lib/'])
        value = self.registry.read_source('lib/main.dart', repository=PROJECT, revision=grant['revision'], path_prefixes=['lib/'])
        self.assertTrue(value['allowModelExport'])
        with self.assertRaises(RepoError):
            self.registry.read_source('README.md',repository=PROJECT,revision=grant['revision'],path_prefixes=['README.md'])
        self.registry.authorize_source(PROJECT,False)
        with self.assertRaises(RepoError):
            self.registry.read_source('lib/main.dart',repository=PROJECT,path_prefixes=['lib/'])
        self.assertFalse(self.registry.source_repos()['repositories'][0]['allowModelExport'])

    def test_scope_grant_never_inherits_to_other_repo_or_new_provider(self):
        other = MockSourceAdapter(OTHER,private=True)
        registry = SourceRegistry(self.notes,lambda:'unused',repositories=(PROJECT,OTHER),
            adapters={PROJECT:self.source,OTHER:other},provider_version=lambda:self.provider[0])
        meta = registry.source_repos()['repositories'][0]
        registry.authorize_source(PROJECT,True,meta['revision'],'provider-1',['lib/'])
        with self.assertRaises(RepoError):
            registry.search_source('source',repository=OTHER,path_prefixes=['lib/'])
        self.provider[0] = 'provider-2'
        self.assertFalse(registry.source_repos()['repositories'][0]['allowModelExport'])
        with self.assertRaises(RepoError):
            registry.search_source('source',repository=PROJECT,path_prefixes=['lib/'])

    def test_stale_grant_version_and_invalid_prefix_are_denied(self):
        metadata = self.grant()['repositories'][0]
        old_revision = metadata['revision']
        self.source._files['lib/main.dart'] = 'New implementation version not automatically authorized.\n'
        self.source._save()
        with self.assertRaises(RepoError) as error:
            self.registry.authorize_source(PROJECT,True,old_revision,'provider-1',['lib/'])
        self.assertEqual(error.exception.code,'source_version')
        current = self.registry.source_repos()['repositories'][0]
        self.assertFalse(current['allowModelExport'])
        for prefixes in ([],[''],['/'],['../'],['lib'],['lib-secret/'],['native/'],['lib/../'],['README.md/']):
            with self.assertRaises(RepoError, msg=str(prefixes)):
                self.registry.authorize_source(PROJECT,True,current['revision'],'provider-1',prefixes)
        with self.assertRaises(RepoError):
            self.registry.authorize_source(PROJECT,True,current['revision'],'different-provider',['lib/'])

    def test_monorepo_prefixes_are_code_specific_not_whole_packages_or_native(self):
        files = {'packages/infrastructure/network_transport/lib/src/runtime.dart':'class Runtime {}\n',
            'native/network_core/crates/network-core/src/lib.rs':'pub fn source() {}\n',
            'packages/infrastructure/credentials.json':'not allowed', 'native/device-secrets.json':'not allowed',
            'README.md':'# Monorepo\n'}
        source = MockSourceAdapter(PROJECT,files,private=True)
        registry = SourceRegistry(self.notes,lambda:'unused',repositories=(PROJECT,),adapters={PROJECT:source})
        meta = registry.source_repos()['repositories'][0]
        self.assertIn('packages/infrastructure/network_transport/lib/',meta['allowedPathPrefixes'])
        self.assertIn('native/network_core/crates/',meta['allowedPathPrefixes'])
        self.assertNotIn('packages/',meta['allowedPathPrefixes'])
        self.assertNotIn('native/',meta['allowedPathPrefixes'])
        for path in list(files)[:2]:
            self.assertEqual(registry.read_source(path,repository=PROJECT)['repository'],PROJECT)
        for path in ('packages/infrastructure/credentials.json','native/device-secrets.json'):
            with self.assertRaises(RepoError): registry.read_source(path,repository=PROJECT)

    def test_search_is_bounded_literal_and_reports_omissions(self):
        self.source._files = {'lib/item%d.dart'%i:'// common source result %d\n'%i for i in range(170)}
        self.source._save()
        value = self.registry.search_source('common source',repository=PROJECT)
        self.assertEqual(len(value['results']),30)
        self.assertTrue(value['truncated'])
        self.assertLessEqual(value['filesScanned'],150)
        self.assertTrue(all(item['repository']==PROJECT and item['revision']==value['revision'] for item in value['results']))
        regex = self.registry.search_source('.*',repository=PROJECT)
        self.assertEqual(regex['results'],[])
        self.assertTrue(regex['truncated'])

    def test_blob_mismatch_and_oversized_range_denied(self):
        with self.assertRaises(RepoError):
            self.registry.read_source('lib/main.dart',1,201,repository=PROJECT)
        source_read = self.source.read
        self.source.read = lambda *args: 'tampered different bytes'
        with self.assertRaises(RepoError) as error:
            self.registry.read_source('lib/main.dart',repository=PROJECT)
        self.assertEqual(error.exception.code,'source_invalid')
        self.source.read = source_read

    def test_late_authorization_cannot_resurrect_a_revoked_grant(self):
        meta = self.registry.source_repos()['repositories'][0]
        entered, release = threading.Event(), threading.Event()
        original = self.source.metadata
        def delayed_metadata():
            entered.set()
            if not release.wait(3):
                raise AssertionError('test release missing')
            return original()
        self.source.metadata = delayed_metadata
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(self.registry.authorize_source, PROJECT, True, meta['revision'], 'provider-1', ['lib/'])
            self.assertTrue(entered.wait(3))
            self.registry.authorize_source(PROJECT, False)
            release.set()
            with self.assertRaises(RepoError):
                pending.result(timeout=3)
        self.assertFalse(self.registry.source_repos()['repositories'][0]['allowModelExport'])

    def test_export_read_finishing_after_revocation_is_not_returned(self):
        meta = self.grant()['repositories'][0]
        entered, release = threading.Event(), threading.Event()
        original = self.source.read
        def delayed_read(*args):
            entered.set()
            if not release.wait(3):
                raise AssertionError('test release missing')
            return original(*args)
        self.source.read = delayed_read
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(self.registry.read_source, 'lib/main.dart', 1, 1, PROJECT, meta['revision'], ['lib/'])
            self.assertTrue(entered.wait(3))
            self.registry.authorize_source(PROJECT, False)
            release.set()
            with self.assertRaises(RepoError) as error:
                pending.result(timeout=3)
            self.assertEqual(error.exception.code, 'source_consent')

    def test_unknown_visibility_is_conservatively_marked_and_disclosed(self):
        original = self.source.metadata
        def unknown_visibility():
            return original() | {'private': True, 'visibilityVerified':False}
        self.source.metadata = unknown_visibility
        meta = self.registry.source_repos()['repositories'][0]
        self.assertIs(meta['private'], True)
        self.assertIs(meta['visibilityVerified'], False)
        self.assertIn('保守', meta['versionNote'])

    def test_wrapper_private_publication_gate_delegates_to_notes_only(self):
        wrapper = RepositoryWithSources(self.notes,self.registry)
        edit = wrapper.editable('docs/sample.md#a01')
        draft = wrapper.preview(dict(edit,operation='update',answerMarkdown='AI proposed answer retains the correct version and implementation boundary.'))
        wrapper.mark_private_proposal(draft['draftId'],{'repository':PROJECT,'revision':self.source.head(),'private':True})
        with self.assertRaises(RepoError): wrapper.commit(draft['draftId'],'public_gate_0123456789')
        wrapper.commit(draft['draftId'],'public_gate_0123456789',confirm_public_publication=True)
        self.assertEqual(len(self.notes_adapter.commits),1)
        self.assertEqual(len(self.source.commits),0)

if __name__ == '__main__': unittest.main()
