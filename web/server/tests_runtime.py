import tempfile
import unittest
from unittest.mock import patch
from .tests_auth import config
from .repository import MemoryAdapter, REPOSITORY, RepoError
from .runtime import build_services
from .sources import RepositoryWithSources
from .config import ConfigurationError


class RuntimeTests(unittest.TestCase):
    def test_private_content_cache_cannot_be_under_static_root(self):
        with tempfile.TemporaryDirectory() as directory:
            cfg = config(static_root=directory, data_cache_root=directory+'/cache')
            with patch('web.server.runtime.GitHubAdapter'):
                with self.assertRaises(ConfigurationError):
                    build_services(cfg)

    def test_https_wiring_uses_registry_and_read_access_does_not_enable_write(self):
        adapter=MemoryAdapter({'docs/fixture.md':'# Fixture\n\n### A01 Question\n\nA sufficiently complete fixture answer.\n'})
        with patch('web.server.runtime.GitHubAdapter',return_value=adapter):
            repo,model=build_services(config())
        self.assertIsInstance(repo,RepositoryWithSources)
        self.assertIs(model.repository,repo)
        self.assertEqual(repo.registry.provider_version(),model.public_settings()['configVersion'])
        self.assertFalse(model.public_settings()['configured'])
        original=repo.editable('docs/fixture.md#a01')
        draft=repo.preview({**original,'operation':'update','answerMarkdown':'A changed but still complete fixture answer.'})
        with self.assertRaises(RepoError) as error:
            repo.commit(draft['draftId'],'runtime_idem_no_write')
        self.assertEqual(error.exception.code,'write_disabled')
        self.assertEqual(adapter.commits,[])

    def test_ssh_wiring_explicit_notes_write_and_readonly_registered_sources(self):
        created=[]
        def factory(name,cache,allow_write=False):
            created.append((name,cache,allow_write))
            adapter=MemoryAdapter({'docs/a.md':'# Fixture\n\n### A01 Question\n\nA complete fixture answer.\n'})
            adapter.repository=name
            return adapter
        with tempfile.TemporaryDirectory() as directory:
            cfg=config(github_transport='ssh',github_cache_root=directory,github_write_enabled=True,
                       source_repositories=(REPOSITORY,'hejulian2004/ssh_mobile'))
            with patch('web.server.git_transport.GitSSHAdapter',side_effect=factory):
                repo,model=build_services(cfg)
            self.assertTrue(repo.notes_repository.adapter.enabled)
            self.assertEqual([(name,write) for name,_,write in created],
                [(REPOSITORY,True),(REPOSITORY,False),('hejulian2004/ssh_mobile',False)])
            self.assertNotEqual(created[0][1],created[1][1])
            self.assertIs(model.repository,repo)
            self.assertEqual(repo.notes_repository._disk.root, created[0][1].parent/'content')
            self.assertEqual(repo.registry._disk.root, repo.notes_repository._disk.root)
