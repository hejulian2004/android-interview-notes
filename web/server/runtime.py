"""Production service wiring. No credential discovery or network call at import."""
from pathlib import Path
from .ai import ModelService
from .config import github_token_provider
from .repository import ContentRepository, GitHubAdapter, REPOSITORY, RepoError
from .sources import SourceRegistry, RepositoryWithSources


class NotesWriteGate:
    """Reading successfully never enables writes. Only explicit server config can."""
    repository = REPOSITORY

    def __init__(self, adapter, enabled=False):
        if adapter.repository != REPOSITORY:
            raise RepoError('repository_denied', '题库写入目标不是已授权仓库。', 403)
        self.adapter, self.enabled = adapter, enabled is True

    def head(self): return self.adapter.head()
    def tree(self, revision): return self.adapter.tree(revision)
    def read(self, revision, path, entry=None): return self.adapter.read(revision, path, entry)

    def atomic_commit(self, *args, **kwargs):
        if not self.enabled:
            raise RepoError('write_disabled', '服务器尚未明确启用题库写入；读取成功不代表具有写权限。', 403)
        return self.adapter.atomic_commit(*args, **kwargs)


def build_services(config):
    config.validate()
    token_provider = github_token_provider(config)
    source_adapters = None
    if config.github_transport == 'ssh':
        from .git_transport import GitSSHAdapter
        root = Path(config.github_cache_root)
        adapter = GitSSHAdapter(REPOSITORY, root/'notes-write', allow_write=config.github_write_enabled)
        source_adapters = {name: GitSSHAdapter(name, root/'source-read', allow_write=False)
                           for name in config.source_repositories}
    else:
        adapter = GitHubAdapter(token_provider)
    notes = ContentRepository(NotesWriteGate(adapter, config.github_write_enabled))
    registry = SourceRegistry(notes, token_provider, repositories=config.source_repositories,
                              adapters=source_adapters)
    repository = RepositoryWithSources(notes, registry)
    model = ModelService(config, repository)
    registry.provider_version = lambda: model.public_settings()['configVersion']
    return repository, model
