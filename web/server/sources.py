"""Read-only, explicitly registered GitHub source snapshots and model-export grants.

Only the notes repository is writable, through the separate ContentRepository. Source
adapters expose GET operations only and never discover credentials or execute code.
"""
from __future__ import annotations
import base64
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
import json
import math
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from .repository import REPOSITORY, RepoError, git_sha, valid_path

AUTHORIZED_REPOSITORIES = (
    REPOSITORY,
    'hejulian2004/ssh_mobile',
    'hejulian2004/testDemo',
    'hejulian2004/word-crush-app',
)
_COMMON_ROOTS = ('lib/', 'src/', 'crates/', 'app/src/', 'android/', 'core/', 'tests/')
_NOTES_ROOTS = ('docs/', 'questions/', 'supplements/', 'data/', 'scripts/', 'tests/', 'web/src/', 'web/engine/')
_EXTENSIONS = ('.md', '.py', '.js', '.mjs', '.ts', '.tsx', '.jsx', '.json', '.html', '.css', '.java', '.kt', '.kts', '.rs', '.dart', '.xml', '.toml', '.yaml', '.yml', '.c', '.h', '.cpp', '.hpp')
_SHA = re.compile(r'^[a-f0-9]{40}$')


def _prefix_valid(prefix):
    return isinstance(prefix, str) and len(prefix) <= 500 and valid_path(prefix[:-1] if prefix.endswith('/') else prefix)


def _within(path, prefix):
    return path.startswith(prefix) if prefix.endswith('/') else path == prefix


def _subset(prefix, allowed):
    return prefix == allowed or allowed.endswith('/') and prefix.startswith(allowed)


def _safe_text_path(path):
    if not valid_path(path) or not path.lower().endswith(_EXTENSIONS):
        return False
    parts = path.split('/')
    if any(p.startswith('.') or p.lower() in ('node_modules', 'dist', 'build', 'target', '__pycache__', 'logs', 'backups', 'private', 'vendor') for p in parts):
        return False
    filename = parts[-1].lower()
    if re.match(r'^(?:id_rsa|id_ed25519|credentials?|secrets?)(?:[._-]|$)', filename):
        return False
    if re.fullmatch(r'(?:tokens?|api[_-]?keys?|passwords?)(?:\.[^.]+)?', filename):
        return False
    return True


def _allowed_prefixes(repository, tree):
    paths = [p for p, value in tree.items() if value.get('mode') in ('100644', '100755') and _safe_text_path(p)]
    candidates = list(_NOTES_ROOTS if repository == REPOSITORY else _COMMON_ROOTS)
    # These are specific documented SSH Mobile monorepo code roots, not general
    # permission to read all files below native/ or packages/.
    if repository == 'hejulian2004/ssh_mobile':
        candidates.append('native/network_core/crates/')
        for path in paths:
            match = re.match(r'^(packages/[^/]+/(?:[^/]+/)?lib/)', path)
            if match:
                candidates.append(match[1])
    candidates.append('README.md')
    return sorted({p for p in candidates if any(_within(path, p) for path in paths)})


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class ReadOnlyGitHubAdapter:
    """A fixed selected repository, HTTPS API host, GET only, no proxy/redirects."""
    def __init__(self, token_provider, repository, timeout=8):
        if repository not in AUTHORIZED_REPOSITORIES:
            raise RepoError('repository_denied', '源码仓库未被明确授权注册。', 403)
        self.repository, self.token_provider, self.timeout = repository, token_provider, timeout
        self._opener = build_opener(ProxyHandler({}), _NoRedirect())

    def _get(self, suffix):
        if not isinstance(suffix, str) or (suffix and not suffix.startswith('/')) or '\r' in suffix or '\n' in suffix:
            raise RepoError('invalid_source_request', '无效源码读取请求。')
        token = self.token_provider()
        if not isinstance(token, str) or not token or '\r' in token or '\n' in token:
            raise RepoError('github_unconfigured', '服务器 GitHub 凭据尚未配置。', 503)
        request = Request('https://api.github.com/repos/' + self.repository + suffix,
            headers={'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer ' + token,
                'User-Agent': 'android-study-source-reader', 'X-GitHub-Api-Version': '2022-11-28'}, method='GET')
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                raw = response.read(5_000_001)
                if len(raw) > 5_000_000:
                    raise RepoError('source_limit', '源码 API 响应超过安全限制。', 502)
                return json.loads(raw)
        except HTTPError as error:
            if error.code in (401, 403, 404):
                raise RepoError('source_unavailable', '仓库不存在、不可见或服务器凭据无读取权限。', 403) from None
            raise RepoError('source_unavailable', 'GitHub 源码读取失败，请稍后重试。', 502) from None
        except (URLError, OSError, TimeoutError, ValueError):
            raise RepoError('source_unavailable', 'GitHub 源码服务暂不可用。', 503) from None

    def metadata(self):
        value = self._get('')
        if (not isinstance(value, dict) or not isinstance(value.get('full_name'), str)
                or value['full_name'].casefold() != self.repository.casefold()
                or type(value.get('private')) is not bool
                or not isinstance(value.get('default_branch'), str)
                or not 1 <= len(value['default_branch']) <= 200
                or any(c in value['default_branch'] for c in ('\r', '\n', '\x00'))):
            raise RepoError('source_invalid', 'GitHub 仓库元信息未通过核验。', 502)
        return {'repository': self.repository, 'private': value['private'], 'defaultBranch': value['default_branch']}

    def head(self, default_branch):
        value = self._get('/git/ref/heads/' + quote(default_branch, safe=''))
        sha = value.get('object', {}).get('sha')
        if not isinstance(sha, str) or not _SHA.fullmatch(sha):
            raise RepoError('source_invalid', 'GitHub 源码版本无效。', 502)
        return sha

    def tree(self, revision):
        if not isinstance(revision, str) or not _SHA.fullmatch(revision):
            raise RepoError('invalid_revision', '源码必须固定到完整提交 SHA。')
        value = self._get('/git/trees/' + revision + '?recursive=1')
        if not isinstance(value, dict) or value.get('truncated') or not isinstance(value.get('tree'), list) or len(value['tree']) > 20000:
            raise RepoError('source_limit', '源码树不完整或过大，未使用不完整索引。', 502)
        tree = {}
        for entry in value['tree']:
            if (isinstance(entry, dict) and entry.get('type') == 'blob' and valid_path(entry.get('path'))
                    and isinstance(entry.get('sha'), str) and _SHA.fullmatch(entry['sha'])
                    and type(entry.get('size', 0)) is int):
                tree[entry['path']] = {'sha': entry['sha'], 'mode': entry.get('mode'), 'size': entry.get('size', 0)}
        return tree

    def read(self, revision, path, entry):
        if not isinstance(revision, str) or not _SHA.fullmatch(revision) or not valid_path(path) or entry.get('mode') not in ('100644', '100755'):
            raise RepoError('path_denied', '只允许读取固定版本的普通源码文件。', 403)
        if not 0 <= entry.get('size', 0) <= 300_000:
            raise RepoError('source_limit', '源码文件超过 300KB 限制。', 413)
        value = self._get('/git/blobs/' + entry['sha'])
        try:
            if value.get('encoding') != 'base64':
                raise ValueError()
            raw = base64.b64decode(value['content'])
            if len(raw) > 300_000 or b'\0' in raw or git_sha(raw) != entry['sha']:
                raise ValueError()
            return raw.decode('utf-8')
        except (ValueError, UnicodeError, KeyError, AttributeError):
            raise RepoError('source_invalid', '目标不是完整有效的 UTF-8 源码。', 422) from None


class SourceRegistry:
    def __init__(self, notes_repository, token_provider, repositories=(REPOSITORY,), adapters=None,
                 clock=time.time, metadata_ttl=120, provider_version=None, cache_root=None):
        if not isinstance(repositories, (tuple, list)) or not repositories or len(repositories) > 4 or len(set(repositories)) != len(repositories):
            raise RepoError('repository_denied', '请显式配置唯一的源码仓库列表。', 403)
        if any(repo not in AUTHORIZED_REPOSITORIES for repo in repositories):
            raise RepoError('repository_denied', '源码仓库超出明确授权范围。', 403)
        adapters = adapters or {}
        if any(repo not in repositories for repo in adapters):
            raise RepoError('repository_denied', '模拟读取器不在注册列表内。', 403)
        self.notes_repository = notes_repository
        self.repositories, self.clock, self.metadata_ttl = tuple(repositories), clock, metadata_ttl
        self.provider_version = provider_version
        self._adapters = {name: adapters.get(name) or ReadOnlyGitHubAdapter(token_provider, name) for name in self.repositories}
        if any(adapter.repository != name for name, adapter in self._adapters.items()):
            raise RepoError('repository_denied', '源码读取器身份与注册仓库不一致。', 403)
        self._snapshots, self._texts, self._grants, self._authorization_versions = {}, {}, {}, {}
        self._indexes, self._refreshing, self._failures, self._text_flights = {}, {}, {}, {}
        self._snapshot_epochs, self._text_failures = {}, {}
        self._text_bytes, self._index_bytes = 0, 0
        self._lock = threading.Lock()
        self._outbound = threading.BoundedSemaphore(4)
        self._disk = None
        if cache_root is not None:
            from .cache import DiskCache
            self._disk = DiskCache(cache_root, 'source-v1', clock=clock)
            # Read only explicitly registered repositories. Persisted grants are
            # deliberately unsupported: a restart requires model consent again.
            for name in self.repositories:
                value = self._disk_get('snapshot:' + name)
                if self._valid_snapshot(value, name) and 0 <= value['checkedAt'] <= self.clock() + 5:
                    self._snapshots[name] = value

    def _disk_get(self, key):
        try:
            return self._disk.get(key) if self._disk else None
        except (OSError, ValueError, TypeError):
            return None

    def _disk_put(self, key, value):
        try:
            return self._disk.put(key, value) if self._disk else False
        except (OSError, ValueError, TypeError):
            return False

    @staticmethod
    def _valid_snapshot(value, name):
        if (not isinstance(value, dict) or set(value) != {'repository', 'private', 'visibilityVerified', 'defaultBranch', 'revision', 'tree', 'allowedPathPrefixes', 'checkedAt'}
                or value.get('repository') != name
                or not isinstance(value.get('revision'), str) or not _SHA.fullmatch(value['revision'])
                or type(value.get('private')) is not bool or type(value.get('visibilityVerified')) is not bool
                or not isinstance(value.get('defaultBranch'), str) or not 1 <= len(value['defaultBranch']) <= 200
                or any(c in value['defaultBranch'] for c in ('\r', '\n', '\x00'))
                or type(value.get('checkedAt')) not in (int, float) or not 0 <= value['checkedAt'] <= 10**12
                or not math.isfinite(value['checkedAt'])
                or not isinstance(value.get('tree'), dict) or len(value['tree']) > 20000):
            return False
        for path, entry in value['tree'].items():
            if (not _safe_text_path(path) or not isinstance(entry, dict)
                    or not set(entry).issubset({'sha', 'mode', 'size', 'sizeKnown'})
                    or ('sizeKnown' in entry and type(entry['sizeKnown']) is not bool)
                    or entry.get('mode') not in ('100644', '100755')
                    or not isinstance(entry.get('sha'), str) or not _SHA.fullmatch(entry['sha'])
                    or type(entry.get('size', 0)) is not int or not 0 <= entry.get('size', 0) <= 300_000):
                return False
        prefixes = _allowed_prefixes(name, value['tree'])
        return (value.get('allowedPathPrefixes') == prefixes
                and all(any(_within(path, p) for p in prefixes) for path in value['tree'])
                and (value['visibilityVerified'] or value['private']))

    def _network(self, call, *args):
        if not self._outbound.acquire(timeout=2):
            raise RepoError('source_busy', '源码读取并发已达上限，请稍后重试。', 429)
        try:
            return call(*args)
        finally:
            self._outbound.release()

    def _selected(self, repository):
        name = REPOSITORY if repository is None else repository
        if not isinstance(name, str) or name not in self._adapters:
            raise RepoError('repository_denied', '源码仓库未由管理员明确注册，未发起请求。', 403)
        return name

    def _fetch_snapshot(self, name, epoch):
        adapter = self._adapters[name]
        meta = self._network(adapter.metadata)
        if (not isinstance(meta, dict) or meta.get('repository', name) != name
                or type(meta.get('private')) is not bool or not isinstance(meta.get('defaultBranch'), str)
                or not 1 <= len(meta['defaultBranch']) <= 200
                or any(c in meta['defaultBranch'] for c in ('\r', '\n', '\x00'))):
            raise RepoError('source_invalid', '源码隐私状态或默认分支未核验。', 502)
        revision = self._network(adapter.head, meta['defaultBranch'])
        if not isinstance(revision, str) or not _SHA.fullmatch(revision):
            raise RepoError('source_invalid', '源码固定版本无效。', 502)
        # The fixed commit tree is immutable; unchanged HEAD needs only a
        # metadata/HEAD check, no clone/index work or per-file network reads.
        with self._lock:
            old = self._snapshots.get(name)
        tree = old['tree'] if old and old['revision'] == revision else self._network(adapter.tree, revision)
        if not isinstance(tree, dict) or len(tree) > 20000:
            raise RepoError('source_limit', '源码索引过大或无效。', 502)
        # Never persist secret/dotfile metadata or contents, links, binaries or
        # unregistered roots. The same filter is applied to in-memory snapshots.
        safe_tree = {path: {k: entry[k] for k in ('sha', 'mode', 'size', 'sizeKnown') if k in entry} for path, entry in tree.items()
                     if _safe_text_path(path) and isinstance(entry, dict)
                     and entry.get('mode') in ('100644', '100755')
                     and isinstance(entry.get('sha'), str) and _SHA.fullmatch(entry['sha'])
                     and type(entry.get('size', 0)) is int and 0 <= entry.get('size', 0) <= 300_000}
        prefixes = _allowed_prefixes(name, safe_tree)
        safe_tree = {path: entry for path, entry in safe_tree.items() if any(_within(path, p) for p in prefixes)}
        verified = meta.get('visibilityVerified', True) is True
        snapshot = {'repository': name, 'private': meta['private'] if verified else True,
            'visibilityVerified': verified, 'defaultBranch': meta['defaultBranch'],
            'revision': revision, 'tree': safe_tree, 'allowedPathPrefixes': _allowed_prefixes(name, safe_tree),
            'checkedAt': self.clock()}
        if not self._valid_snapshot(snapshot, name):
            raise RepoError('source_invalid', '源码缓存索引未通过完整性核验。', 502)
        with self._lock:
            if self._snapshot_epochs.get(name, 0) != epoch:
                raise RepoError('source_invalidated', '源码索引已由成功提交失效，旧后台结果没有替换缓存。', 409)
            self._snapshots[name] = snapshot
            self._failures.pop(name, None)
            grant = self._grants.get(name)
            if grant and (grant['revision'] != revision or any(not any(_subset(p, allowed) for allowed in snapshot['allowedPathPrefixes']) for p in grant['pathPrefixes'])):
                self._grants.pop(name, None)
            # The invalidation generation and disk replacement share this lock.
            self._disk_put('snapshot:' + name, snapshot)
        return snapshot

    def _refresh_worker(self, name, event, epoch):
        try:
            self._fetch_snapshot(name, epoch)
        except Exception as error:
            # No raw transport messages, credentials or exception objects enter
            # persistent cache or API results. Bounded exponential retry delay.
            with self._lock:
                if self._snapshot_epochs.get(name, 0) != epoch:
                    return
                failures = self._failures.get(name, {}).get('count', 0) + 1
                self._failures[name] = {'count': min(failures, 8),
                    'retryAt': self.clock() + min(300, 5 * 2 ** min(failures - 1, 6)),
                    'code': error.code if isinstance(error, RepoError) else 'source_unavailable'}
        finally:
            with self._lock:
                self._refreshing.pop(name, None)
                event.set()

    def _start_refresh(self, name, force=False):
        with self._lock:
            event = self._refreshing.get(name)
            if event is not None:
                return event
            if not force and self._failures.get(name, {}).get('retryAt', 0) > self.clock():
                return None
            event = threading.Event()
            self._refreshing[name] = event
            epoch = self._snapshot_epochs.get(name, 0)
        try:
            threading.Thread(target=self._refresh_worker, args=(name, event, epoch),
                             name='study-source-refresh', daemon=True).start()
        except RuntimeError:
            with self._lock:
                if self._refreshing.get(name) is event:
                    self._refreshing.pop(name, None)
                if self._snapshot_epochs.get(name, 0) == epoch:
                    self._failures[name] = {'count': 1, 'retryAt': self.clock() + 5, 'code': 'source_busy'}
                event.set()
        return event

    def _snapshot(self, repository, force=False):
        name = self._selected(repository)
        with self._lock:
            old = self._snapshots.get(name)
        if old and not force:
            if not 0 <= self.clock() - old['checkedAt'] < self.metadata_ttl:
                self._start_refresh(name)
            return old
        event = self._start_refresh(name, force=force)
        if event is None:
            raise RepoError('source_unavailable', '源码更新暂不可用，正在等待重试。', 503)
        if not event.wait(35):
            raise RepoError('source_timeout', '源码版本核验超时，后台检查仍在进行。', 503)
        with self._lock:
            current, failure = self._snapshots.get(name), self._failures.get(name)
        if failure or current is None:
            raise RepoError('source_unavailable', '源码当前无法核验，已有固定版本缓存会保留。', 503)
        return current

    def invalidate(self, repository, confirmed_revision):
        """Invalidate only after an adapter has confirmed a real GitHub commit.

        Old immutable blobs remain reusable, but no old current-version tree or
        model-export grant can survive this generation or return after restart.
        """
        if repository not in self._adapters or not isinstance(confirmed_revision, str) or not _SHA.fullmatch(confirmed_revision):
            return
        with self._lock:
            old = self._snapshots.get(repository)
            if old and old['revision'] == confirmed_revision:
                return
            self._snapshot_epochs[repository] = self._snapshot_epochs.get(repository, 0) + 1
            self._snapshots.pop(repository, None)
            self._grants.pop(repository, None)
            self._failures.pop(repository, None)
            if self._disk:
                self._disk.delete('snapshot:' + repository)

    def _grant(self, snapshot):
        with self._lock:
            grant = copy.deepcopy(self._grants.get(snapshot['repository']))
        if not grant or grant['revision'] != snapshot['revision']:
            return None
        if self.provider_version is not None and grant['providerConfigVersion'] != self.provider_version():
            return None
        return grant

    def _metadata(self, repository):
        try:
            if self._disk:
                with self._lock:
                    snapshot = self._snapshots.get(repository)
                if snapshot is None:
                    with self._lock:
                        failed = repository in self._failures
                    if failed:
                        raise RepoError('source_unavailable', '源码目前无法读取，请稍后重试。', 503)
                    raise RepoError('source_pending', '源码索引正在后台准备，请稍后刷新。', 503)
                if not 0 <= self.clock() - snapshot['checkedAt'] < self.metadata_ttl:
                    self._start_refresh(repository)
            else:
                snapshot = self._snapshot(repository)
            grant = self._grant(snapshot)
            with self._lock:
                refreshing = repository in self._refreshing
                failed = repository in self._failures
            status = 'stale' if failed or not 0 <= self.clock() - snapshot['checkedAt'] < self.metadata_ttl else 'fresh'
            return {key: copy.deepcopy(snapshot[key]) for key in ('repository', 'private', 'visibilityVerified', 'revision', 'defaultBranch', 'allowedPathPrefixes')} | {
                'available': True, 'allowModelExport': grant is not None, 'authorization': grant,
                'cacheStatus': status, 'checkedAt': snapshot['checkedAt'], 'refreshing': refreshing,
                'versionNote': '注册仓库当前默认分支的固定提交；不能自动等同笔记中记录的历史实现。' + ('' if snapshot['visibilityVerified'] else ' 仓库可见性未独立核验，按私有源码保守处理。')}
        except Exception as error:
            # Per-repository failures never break note editing or disclose credentials.
            code = error.code if isinstance(error, RepoError) else 'source_unavailable'
            return {'repository': repository, 'available': False, 'pending': code == 'source_pending', 'private': None, 'revision': None,
                'allowedPathPrefixes': [], 'allowModelExport': False, 'authorization': None,
                'error': {'code': code, 'message': '源码索引正在后台准备，请稍后刷新。' if code == 'source_pending' else '该仓库当前无法读取；请检查服务器读取权限或稍后重试。'}}

    def source_repos(self):
        if self._disk:
            # Cold repository metadata is progressively warmed by one daemon;
            # no request waits for every source repository clone/index.
            with self._lock:
                cold = [name for name in self.repositories if name not in self._snapshots]
                prewarming = getattr(self, '_prewarming', False)
                should_start = bool(cold) and not prewarming and self.clock() >= getattr(self, '_prewarm_retry_at', 0)
                if should_start:
                    self._prewarming = True
            if should_start:
                def prewarm():
                    try:
                        for name in cold:
                            event = self._start_refresh(name)
                            if event is not None:
                                event.wait(35)
                    finally:
                        with self._lock:
                            self._prewarming = False
                try:
                    threading.Thread(target=prewarm, name='study-source-prewarm', daemon=True).start()
                except RuntimeError:
                    with self._lock:
                        self._prewarming = False
                        self._prewarm_retry_at = self.clock() + 5
            return {'repositories': [self._metadata(name) for name in self.repositories]}
        output = {}
        pool = ThreadPoolExecutor(max_workers=min(4, len(self.repositories)), thread_name_prefix='study-source-meta')
        futures = {pool.submit(self._metadata, name): name for name in self.repositories}
        try:
            for future in as_completed(futures, timeout=35):
                output[futures[future]] = future.result()
        except FuturesTimeout:
            pass
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        return {'repositories': [output.get(name) or {'repository': name, 'available': False, 'private': None,
            'revision': None, 'allowedPathPrefixes': [], 'allowModelExport': False, 'authorization': None,
            'error': {'code': 'source_timeout', 'message': '源码版本核验超时，未使用未经核验的版本。'}} for name in self.repositories]}

    def authorize_source(self, repository, allow_model_export, revision=None, provider_config_version=None, path_prefixes=None):
        name = self._selected(repository)
        if type(allow_model_export) is not bool:
            raise RepoError('source_consent', '请明确允许或撤销源码外发授权。')
        with self._lock:
            authorization_version = self._authorization_versions.get(name, 0) + 1
            self._authorization_versions[name] = authorization_version
        if not allow_model_export:
            with self._lock:
                self._grants.pop(name, None)
            return self.source_repos()
        if not isinstance(provider_config_version, str) or not 1 <= len(provider_config_version) <= 160:
            raise RepoError('source_consent', '源码外发授权必须绑定当前模型供应商配置版本。', 403)
        if self.provider_version is not None and provider_config_version != self.provider_version():
            raise RepoError('source_consent', '模型配置已变化，请重新核对供应商后授权。', 409)
        snapshot = self._snapshot(name, force=True)
        if not isinstance(revision, str) or revision != snapshot['revision']:
            raise RepoError('source_version', '源码版本已变化，请重新查看版本并授权。', 409)
        selected = self._validate_prefixes(path_prefixes, snapshot['allowedPathPrefixes'])
        with self._lock:
            if self._authorization_versions.get(name) != authorization_version:
                raise RepoError('source_consent', '源码授权选择已变化，较早的授权请求未生效。', 409)
            self._grants[name] = {'revision': revision, 'providerConfigVersion': provider_config_version, 'pathPrefixes': selected}
        return self.source_repos()

    @staticmethod
    def _validate_prefixes(prefixes, allowed):
        if not isinstance(prefixes, list) or not 1 <= len(prefixes) <= 20 or len(set(str(p) for p in prefixes)) != len(prefixes):
            raise RepoError('source_scope', '请明确选择一个或多个源码路径范围。', 403)
        if any(not _prefix_valid(prefix) or not any(_subset(prefix, item) for item in allowed) for prefix in prefixes):
            raise RepoError('source_scope', '源码路径范围超出服务器允许范围。', 403)
        return list(prefixes)

    def _context(self, repository, revision, path_prefixes):
        snapshot = self._snapshot(self._selected(repository))
        if revision is not None and revision != snapshot['revision']:
            raise RepoError('source_version', '请求的源码版本不是当前已核验版本，请刷新。', 409)
        scope = snapshot['allowedPathPrefixes']
        if path_prefixes is not None:
            scope = self._validate_prefixes(path_prefixes, scope)
            grant = self._grant(snapshot)
            if not grant or any(not any(_subset(p, item) for item in grant['pathPrefixes']) for p in scope):
                raise RepoError('source_consent', '源码工具范围未被明确授权或授权已失效。', 403)
        return snapshot, scope

    @staticmethod
    def _blob_key(snapshot, path):
        return ':'.join((snapshot['repository'], snapshot['revision'], path, snapshot['tree'][path]['sha']))

    def _read(self, snapshot, path):
        entry = snapshot['tree'].get(path)
        if not entry or entry.get('mode') not in ('100644', '100755') or not _safe_text_path(path):
            raise RepoError('path_denied', '源码路径不在普通文本允许范围内。', 403)
        if type(entry.get('size', 0)) is not int or not 0 <= entry.get('size', 0) <= 300_000:
            raise RepoError('source_limit', '源码文件超过大小限制。', 413)
        key = self._blob_key(snapshot, path)
        with self._lock:
            cached = self._texts.get(key)
            flight = self._text_flights.get(key)
            if cached is not None:
                return cached
            if self._text_failures.get(key, {}).get('retryAt', 0) > self.clock():
                raise RepoError('source_unavailable', '该源码文件暂时无法读取，请稍后重试。', 503)
            if flight is None:
                flight = threading.Event()
                self._text_flights[key] = flight
                owner = True
            else:
                owner = False
        if not owner:
            if not flight.wait(35):
                raise RepoError('source_timeout', '源码读取超时，请稍后重试。', 503)
            with self._lock:
                cached = self._texts.get(key)
            if cached is None:
                raise RepoError('source_unavailable', '源码读取失败，未使用不完整缓存。', 503)
            return cached
        try:
            value = self._disk_get('text:' + key)
            text = value.get('content') if isinstance(value, dict) and all(value.get(k) == v for k, v in
                (('repository', snapshot['repository']), ('revision', snapshot['revision']), ('path', path), ('sha', entry['sha']))) else None
            if not self._valid_text(text, entry['sha']):
                text = self._network(self._adapters[snapshot['repository']].read, snapshot['revision'], path, entry)
                if not self._valid_text(text, entry['sha']):
                    raise RepoError('source_invalid', '源码文件完整性或文本类型无效。', 422)
                self._disk_put('text:' + key, {'repository': snapshot['repository'], 'revision': snapshot['revision'],
                    'path': path, 'sha': entry['sha'], 'content': text})
            with self._lock:
                self._texts[key] = text
                self._text_failures.pop(key, None)
                self._text_bytes += len(text.encode())
                while len(self._texts) > 300 or self._text_bytes > 8_000_000:
                    self._text_bytes -= len(self._texts.pop(next(iter(self._texts))).encode())
            return text
        except Exception:
            with self._lock:
                failures = self._text_failures.get(key, {}).get('count', 0) + 1
                self._text_failures[key] = {'count': min(5, failures),
                    'retryAt': self.clock() + min(60, 5 * 2 ** min(failures - 1, 4))}
                while len(self._text_failures) > 300:
                    self._text_failures.pop(next(iter(self._text_failures)))
            raise
        finally:
            with self._lock:
                self._text_flights.pop(key, None)
                flight.set()

    @staticmethod
    def _valid_text(text, sha):
        return isinstance(text, str) and len(text.encode()) <= 300_000 and '\0' not in text and git_sha(text) == sha

    def _index(self, snapshot, path):
        key = self._blob_key(snapshot, path)
        with self._lock:
            cached = self._indexes.get(key)
        if cached is not None:
            return cached[0]
        text = self._read(snapshot, path)
        value = self._disk_get('index:' + key)
        folded = text.casefold()
        # Persisted literal-search indexes contain no authority. Match their
        # identity and normalized bytes against the verified immutable blob.
        if not (isinstance(value, dict) and value.get('key') == key and value.get('folded') == folded):
            self._disk_put('index:' + key, {'key': key, 'folded': folded})
        index = (text.splitlines(), folded.splitlines())
        with self._lock:
            size = len(text.encode()) + len(folded.encode()) + 64 * (len(index[0]) + len(index[1]))
            if key not in self._indexes:
                self._indexes[key] = (index, size)
                self._index_bytes += size
            while len(self._indexes) > 300 or self._index_bytes > 8_000_000:
                self._index_bytes -= self._indexes.pop(next(iter(self._indexes)))[1]
        return index

    def _cache_state(self, snapshot):
        with self._lock:
            current = self._snapshots.get(snapshot['repository'])
            failed = snapshot['repository'] in self._failures
            refreshing = snapshot['repository'] in self._refreshing
        stale = (failed or current is None or current['revision'] != snapshot['revision']
                 or not 0 <= self.clock() - snapshot['checkedAt'] < self.metadata_ttl)
        return {'cacheStatus': 'stale' if stale else 'fresh',
                'checkedAt': snapshot['checkedAt'], 'refreshing': refreshing}

    @staticmethod
    def _result(snapshot, path, start, end, content):
        url = f'https://github.com/{snapshot["repository"]}/blob/{snapshot["revision"]}/{quote(path, safe="/")}#L{start}-L{end}'
        return {'repository': snapshot['repository'], 'private': snapshot['private'], 'revision': snapshot['revision'],
            'path': path, 'startLine': start, 'endLine': end, 'content': content, 'text': content, 'url': url, 'sourceUrl': url}

    def read_source(self, path, start_line=1, end_line=120, repository=None, revision=None, path_prefixes=None):
        snapshot, scope = self._context(repository, revision, path_prefixes)
        if not _safe_text_path(path) or not any(_within(path, prefix) for prefix in scope):
            raise RepoError('path_denied', '源码路径超出所选允许范围。', 403)
        if type(start_line) is not int or type(end_line) is not int or start_line < 1 or end_line < start_line or end_line-start_line >= 200:
            raise RepoError('source_lines', '每次读取应为有效的 1–200 行。')
        lines = self._read(snapshot, path).splitlines()
        if start_line > max(1, len(lines)):
            raise RepoError('source_lines', '起始行超出文件范围。')
        end_line = min(end_line, len(lines))
        content = '\n'.join(lines[start_line-1:end_line])
        if len(content.encode()) > 40_000:
            raise RepoError('source_limit', '选定代码段过大，请缩小范围。', 413)
        if path_prefixes is not None:
            self._context(repository, snapshot['revision'], path_prefixes)
        return self._result(snapshot, path, start_line, end_line, content) | self._cache_state(snapshot) | {'allowModelExport': self._grant(snapshot) is not None}

    def search_source(self, query, repository=None, revision=None, path_prefixes=None):
        if not isinstance(query, str) or not 2 <= len(query.strip()) <= 160:
            raise RepoError('invalid_query', '源码搜索词应为 2–160 字。')
        snapshot, scope = self._context(repository, revision, path_prefixes)
        candidates = sorted(path for path, entry in snapshot['tree'].items() if _safe_text_path(path)
            and entry.get('mode') in ('100644', '100755') and any(_within(path, prefix) for prefix in scope)
            and type(entry.get('size', 0)) is int and 0 <= entry.get('size', 0) <= 300_000)
        results, scanned, total, result_bytes = [], 0, 0, 0
        deadline = time.monotonic() + 20
        for path in candidates[:150]:
            if time.monotonic() > deadline:
                break
            lines, folded_lines = self._index(snapshot, path)
            total += sum(len(line.encode()) + 1 for line in lines)
            if total > 2_000_000:
                break
            scanned += 1
            for number, (line, folded_line) in enumerate(zip(lines, folded_lines), 1):
                if query.strip().casefold() in folded_line:
                    snippet = line[:700]
                    result_bytes += len(snippet.encode())
                    if result_bytes > 20_000:
                        break
                    results.append(self._result(snapshot, path, number, number, snippet))
                    if len(results) >= 30:
                        break
            if len(results) >= 30 or result_bytes > 20_000:
                break
        if path_prefixes is not None:
            self._context(repository, snapshot['revision'], path_prefixes)
        return {'repository': snapshot['repository'], 'private': snapshot['private'], 'revision': snapshot['revision'],
            'results': results, 'filesScanned': scanned, 'truncated': scanned < len(candidates) or len(results) >= 30 or result_bytes > 20_000,
            'allowModelExport': self._grant(snapshot) is not None, **self._cache_state(snapshot),
            'notice': '有界文本检索，只查询显示的默认分支固定提交；未命中不代表不存在，也不能证明笔记中的历史实现。'}


class RepositoryWithSources:
    """Keep all write operations pinned to the notes repository, regardless of selection."""
    def __init__(self, notes_repository, registry):
        self.notes_repository, self.registry = notes_repository, registry

    def catalog(self, force=False): return self.notes_repository.catalog(force=force)
    def editable(self, question_id, fresh=False): return self.notes_repository.editable(question_id, fresh=fresh)
    def preview(self, change): return self.notes_repository.preview(change)
    def commit(self, draft_id, idempotency_key, actor='admin', confirm_public_publication=False):
        result = self.notes_repository.commit(draft_id, idempotency_key, actor=actor, confirm_public_publication=confirm_public_publication)
        self.registry.invalidate(REPOSITORY, result['commit'])
        return result
    def mark_private_proposal(self, draft_id, disclosure): return self.notes_repository.mark_private_proposal(draft_id, disclosure)
    def source_repos(self): return self.registry.source_repos()
    def authorize_source(self, repository, allow_model_export, revision=None, provider_config_version=None, path_prefixes=None):
        return self.registry.authorize_source(repository, allow_model_export, revision, provider_config_version, path_prefixes)
    def search_source(self, query, repository=None, revision=None, path_prefixes=None):
        return self.registry.search_source(query, repository, revision, path_prefixes)
    def read_source(self, path, start_line=1, end_line=120, repository=None, revision=None, path_prefixes=None):
        return self.registry.read_source(path, start_line, end_line, repository, revision, path_prefixes)
