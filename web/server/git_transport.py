"""Restricted Git-over-SSH storage using the server's existing OpenSSH identity.

No key is discovered, read, copied or printed by this module. OpenSSH uses the service
user's explicitly approved existing identity and known_hosts. Remote code/hooks are
never executed. The optional underscore-prefixed remote resolver is for local tests;
no environment or HTTP input can set it.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import tempfile
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from .repository import REPOSITORY, RepoError, git_sha, valid_path

AUTHORIZED_REPOSITORIES = (REPOSITORY, 'hejulian2004/ssh_mobile', 'hejulian2004/testDemo', 'hejulian2004/word-crush-app')
_SHA = re.compile(r'^[a-f0-9]{40}$')
_TX = re.compile(r'^[A-Za-z0-9_-]{12,128}$')
MAX_FILE_BYTES = 1_500_000
MAX_CACHE_BYTES = 200_000_000
_LOCKS, _LOCKS_GUARD = {}, threading.Lock()


@dataclass
class GitResult:
    returncode: int
    stdout: bytes
    stderr: bytes = b''


def _path_ok(path):
    return valid_path(path) and not any(ord(c) < 32 or ord(c) == 127 for c in path)


def _write_path(path):
    return _path_ok(path) and (path in ('README.md', 'METHODOLOGY.md', 'data/questions.json', 'data/stats.json', 'data/generated-files.json', 'data/web-editor-state.json', 'references/README.md')
        or path.startswith(('docs/', 'questions/', 'supplements/', 'sources/', 'indexes/')) and path.endswith('.md'))


def _directory(path):
    path = Path(path).absolute()
    # Resolve no symlinks; a service cache must never be redirected to another tree.
    for part in (path, *path.parents):
        if part.is_symlink():
            raise RepoError('git_cache_unsafe', 'Git 缓存目录不能包含符号链接。', 503)
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    meta = path.stat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != os.getuid() or meta.st_mode & 0o077:
        raise RepoError('git_cache_unsafe', 'Git 缓存目录必须由服务用户独占且权限为 0700。', 503)
    return path


def _cache_size(path):
    total = 0
    for root, directories, files in os.walk(path, followlinks=False):
        directories[:] = [x for x in directories if not (Path(root) / x).is_symlink()]
        for name in files:
            try:
                info = (Path(root) / name).lstat()
                if stat.S_ISREG(info.st_mode):
                    total += info.st_size
            except FileNotFoundError:
                continue
    return total


def _run_process(argv, *, input=b'', timeout=20, max_output=2_000_000, env=None, cache_dir=None, max_cache_bytes=MAX_CACHE_BYTES):
    """Bound time, output, disk and subprocess descendants; never return raw errors."""
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr, tempfile.TemporaryFile() as stdin:
        stdin.write(input); stdin.seek(0)
        try:
            process = subprocess.Popen(argv, stdin=stdin, stdout=stdout, stderr=stderr, env=env,
                                       start_new_session=True, close_fds=True)
        except OSError:
            raise RepoError('git_unavailable', 'Git/SSH 运行环境不可用。', 503) from None
        deadline, check_disk_at = time.monotonic() + timeout, 0
        try:
            while process.poll() is None:
                now = time.monotonic()
                if now >= deadline:
                    raise RepoError('git_timeout', 'Git/SSH 请求超时，请保留草稿并核实状态。', 503)
                if os.fstat(stdout.fileno()).st_size > max_output or os.fstat(stderr.fileno()).st_size > 262144:
                    raise RepoError('git_limit', 'Git 输出超过安全限制。', 503)
                if cache_dir is not None and now >= check_disk_at:
                    if _cache_size(cache_dir) > max_cache_bytes:
                        raise RepoError('git_cache_limit', '独立 Git 缓存已达大小上限，请管理员核查。', 503)
                    check_disk_at = now + .2
                time.sleep(.02)
            stdout.seek(0); stderr.seek(0)
            out, err = stdout.read(max_output + 1), stderr.read(262145)
            if len(out) > max_output or len(err) > 262144:
                raise RepoError('git_limit', 'Git 输出超过安全限制。', 503)
            if cache_dir is not None and _cache_size(cache_dir) > max_cache_bytes:
                raise RepoError('git_cache_limit', '独立 Git 缓存已达大小上限，请管理员核查。', 503)
            return GitResult(process.returncode, out, err)
        finally:
            if process.poll() is None:
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait()


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None


class GitSSHAdapter:
    def __init__(self, repository, cache_root, allow_write=False, *, timeout=20, runner=None,
                 metadata_fetcher=None, max_cache_bytes=MAX_CACHE_BYTES, _test_remote_resolver=None):
        if repository not in AUTHORIZED_REPOSITORIES:
            raise RepoError('repository_denied', 'Git 仓库未在服务端明确注册。', 403)
        if allow_write and repository != REPOSITORY:
            raise RepoError('repository_read_only', '项目源码仓库只允许读取。', 403)
        if type(allow_write) is not bool or not 1 <= timeout <= 60 or not 1_000_000 <= max_cache_bytes <= 500_000_000:
            raise RepoError('git_configuration', 'Git 适配器配置无效。', 503)
        self.repository, self.allow_write, self.timeout = repository, allow_write, timeout
        public_root = Path(__file__).resolve().parents[1]
        requested_root = Path(cache_root).absolute()
        if requested_root == public_root or public_root in requested_root.parents:
            raise RepoError('git_cache_unsafe', 'Git 缓存必须在 Web 项目目录之外。', 503)
        self._root = _directory(requested_root)
        self.path = self._root / (repository.replace('/', '--') + '.git')
        self.path = _directory(self.path)
        with _LOCKS_GUARD:
            self._lock = _LOCKS.setdefault(str(self.path), threading.RLock())
        self._runner, self._metadata_fetcher = runner or _run_process, metadata_fetcher or self._public_metadata
        self._max_cache_bytes, self._test_mode = max_cache_bytes, _test_remote_resolver is not None
        self.remote = ('ssh://git@github.com/' + repository + '.git') if not self._test_mode else str(_test_remote_resolver(repository))
        if any(c in self.remote for c in ('\r', '\n', '\x00')):
            raise RepoError('git_configuration', 'Git 测试地址无效。', 503)
        self._known_revisions = set()
        self._metadata_cache = None
        with self._lock:
            if not (self.path / 'HEAD').exists():
                self._git(['init', '--bare', '--template=', '--initial-branch=main', str(self.path)], outside=True)
            if self._git(['rev-parse', '--is-bare-repository']).stdout.strip() != b'true':
                raise RepoError('git_cache_unsafe', 'Git 缓存不是独立裸仓库。', 503)
            # Set only this new private cache's remote. No user/global SSH/Git config changes.
            for name, value in (('remote.origin.url', self.remote), ('remote.origin.promisor', 'true'),
                                ('remote.origin.partialclonefilter', 'blob:none'), ('extensions.partialClone', 'origin')):
                self._git(['config', '--local', name, value])
            self._transactions = self._load_transactions()

    def _env(self, extra=None):
        env = {name: os.environ[name] for name in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'SSH_AUTH_SOCK') if name in os.environ}
        env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0',
            GIT_ASKPASS='/bin/false', SSH_ASKPASS='/bin/false', GIT_LFS_SKIP_SMUDGE='1',
            GIT_SSH_COMMAND='ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=12 -o ForwardAgent=no',
            GIT_AUTHOR_NAME='Android Study Editor', GIT_AUTHOR_EMAIL='android-study@localhost.invalid',
            GIT_COMMITTER_NAME='Android Study Editor', GIT_COMMITTER_EMAIL='android-study@localhost.invalid')
        if extra: env.update(extra)
        return env

    def _git(self, args, *, input=b'', check=True, outside=False, extra_env=None, limit=2_000_000):
        command = ['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', '-c', 'gc.auto=0',
                   '-c', 'maintenance.auto=false', '-c', 'commit.gpgsign=false', '-c', 'protocol.allow=never',
                   '-c', 'protocol.ssh.allow=always', '-c', 'protocol.ext.allow=never',
                   '-c', 'protocol.file.allow=' + ('always' if self._test_mode else 'never')]
        if not outside: command += ['--git-dir=' + str(self.path)]
        result = self._runner(command + args, input=input, timeout=self.timeout, max_output=limit,
                              env=self._env(extra_env), cache_dir=self.path, max_cache_bytes=self._max_cache_bytes)
        if check and result.returncode:
            raise RepoError('git_unavailable', 'Git/SSH 请求失败；请检查现有身份、仓库权限或网络，不会回退其他凭据。', 503)
        return result

    @staticmethod
    def _branch(branch):
        if (not isinstance(branch, str) or not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9._/-]{0,199}', branch)
                or any(x in branch for x in ('..', '//', '@{')) or branch.endswith(('/', '.', '.lock'))
                or any(x.startswith('.') or x.endswith('.lock') for x in branch.split('/'))):
            raise RepoError('invalid_revision', 'Git 分支名称无效。')
        return branch

    def _remote_head(self, branch=None):
        args = ['ls-remote', '--symref', self.remote, 'HEAD'] if branch is None else ['ls-remote', '--exit-code', self.remote, 'refs/heads/' + self._branch(branch)]
        text = self._git(args, limit=65536).stdout.decode('utf-8', errors='strict')
        lines = [line.split('\t', 1) for line in text.splitlines() if '\t' in line]
        reference = 'HEAD' if branch is None else 'refs/heads/' + branch
        matches = [sha for sha, ref in lines if ref == reference and _SHA.fullmatch(sha)]
        if len(matches) != 1:
            raise RepoError('source_unavailable', 'Git 仓库不存在、不可读或没有已核验提交。', 403)
        if branch is None:
            refs = [sha[len('ref: refs/heads/'):] for sha, ref in lines if ref == 'HEAD' and sha.startswith('ref: refs/heads/')]
            if len(refs) != 1:
                raise RepoError('source_invalid', 'Git 默认分支未通过核验。', 502)
            branch = self._branch(refs[0])
        return matches[0], branch

    def head(self, default_branch=None):
        if default_branch is None and self.repository == REPOSITORY:
            default_branch = 'main'
        return self._remote_head(default_branch)[0]

    def _public_metadata(self):
        request = Request('https://api.github.com/repos/' + self.repository,
            headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'android-study-ssh-metadata'})
        try:
            with build_opener(ProxyHandler({}), _NoRedirect()).open(request, timeout=5) as response:
                raw = response.read(65537)
                if len(raw) > 65536: raise ValueError()
                return json.loads(raw)
        except HTTPError as error:
            if error.code == 404: return None
            raise

    def metadata(self):
        with self._lock:
            if self._metadata_cache and time.monotonic() - self._metadata_cache[0] < 60:
                return dict(self._metadata_cache[1])
            revision, branch = self._remote_head()
            private, verified = True, False
            try:
                value = self._metadata_fetcher()
                if value is None:
                    # Git authenticated access plus the public API's 404 is private.
                    verified = True
                elif (isinstance(value, dict) and value.get('full_name', '').casefold() == self.repository.casefold()
                        and type(value.get('private')) is bool and value.get('default_branch') == branch):
                    private, verified = value['private'], True
            except Exception:
                pass  # No credential fallback. Unknown visibility is treated as private.
            result = {'repository': self.repository, 'private': private, 'defaultBranch': branch,
                      'revision': revision, 'visibilityVerified': verified, 'writeCapabilityVerified': False}
            self._metadata_cache = (time.monotonic(), result)
            return dict(result)

    def _ensure_revision(self, revision, depth=1):
        if not isinstance(revision, str) or not _SHA.fullmatch(revision):
            raise RepoError('invalid_revision', 'Git 源码必须固定到完整提交 SHA。')
        with self._lock:
            if revision in self._known_revisions and depth == 1: return
            result = self._git(['cat-file', '-e', revision + '^{commit}'], check=False)
            if result.returncode or depth > 1:
                self._git(['fetch', '--no-tags', '--no-recurse-submodules', '--depth=' + str(depth), '--filter=blob:none', 'origin', revision], limit=262144)
            self._known_revisions.add(revision)
            if len(self._known_revisions) > 1000: self._known_revisions = {revision}

    def tree(self, revision):
        self._ensure_revision(revision)
        raw = self._git(['ls-tree', '-r', '-z', revision], limit=5_000_000).stdout
        result = {}
        for row in raw.split(b'\0'):
            if not row: continue
            try:
                info, path_raw = row.split(b'\t', 1)
                mode, kind, sha = info.decode('ascii').split(' ')
                path = path_raw.decode('utf-8')
            except (ValueError, UnicodeError):
                raise RepoError('source_invalid', 'Git 源码树不是有效文本索引。', 502) from None
            if kind != 'blob' or not _path_ok(path): continue
            if not _SHA.fullmatch(sha): raise RepoError('source_invalid', 'Git 源码树对象无效。', 502)
            # A partial clone intentionally does not download every blob for sizes.
            # read() verifies exact size/hash before returning any content.
            result[path] = {'sha': sha, 'mode': mode, 'size': 0, 'sizeKnown': False}
            if len(result) > 20000: raise RepoError('source_limit', 'Git 源码树超过文件数限制。', 413)
        return result

    def read(self, revision, path, entry=None):
        if not _path_ok(path): raise RepoError('path_denied', 'Git 文件路径不在允许范围。', 403)
        actual = self.tree(revision).get(path)
        if not actual or actual['mode'] not in ('100644', '100755') or entry and entry.get('sha') != actual['sha']:
            raise RepoError('path_denied', 'Git 目标不是已核验的普通文件。', 403)
        sha = actual['sha']
        size = self._git(['cat-file', '-s', sha], limit=100).stdout.strip()
        if not size.isdigit() or int(size) > MAX_FILE_BYTES:
            raise RepoError('file_limit', 'Git 文件超过读取大小限制。', 413)
        raw = self._git(['cat-file', 'blob', sha], limit=MAX_FILE_BYTES).stdout
        if b'\0' in raw or git_sha(raw) != sha:
            raise RepoError('file_invalid', 'Git 文件不是有效文本或完整性校验失败。', 422)
        try: return raw.decode('utf-8')
        except UnicodeError: raise RepoError('file_invalid', 'Git 文件必须是 UTF-8 文本。', 422) from None

    def _load_transactions(self):
        path = self.path / 'study-transactions.json'
        if path.is_symlink():
            raise RepoError('git_cache_unsafe', 'Git 提交状态记录不能是符号链接。', 503)
        if not path.exists(): return {}
        try:
            fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
            with os.fdopen(fd, 'r', encoding='utf-8') as stream:
                meta = os.fstat(stream.fileno())
                if not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.getuid() or meta.st_mode & 0o077 or meta.st_size > 1_000_000: raise ValueError()
                value = json.load(stream)
            if not isinstance(value, dict) or len(value) > 1000: raise ValueError()
            for tx, row in value.items():
                if not _TX.fullmatch(tx) or not isinstance(row, dict) or set(row) != {'candidate', 'expected', 'digest', 'status'} or row['status'] not in ('pending', 'done') or not _SHA.fullmatch(row['candidate']) or not _SHA.fullmatch(row['expected']) or not re.fullmatch(r'[a-f0-9]{64}', row['digest']): raise ValueError()
            return value
        except (OSError, ValueError, TypeError):
            raise RepoError('git_cache_unsafe', 'Git 提交状态记录无效，已阻止写入。', 503) from None

    def _save_transactions(self):
        destination = self.path / 'study-transactions.json'
        fd, name = tempfile.mkstemp(prefix='.transactions-', dir=self.path)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(self._transactions, stream, separators=(',', ':')); stream.flush(); os.fsync(stream.fileno())
            os.replace(name, destination)
        finally:
            if os.path.exists(name): os.unlink(name)

    def _contains(self, head, candidate):
        if head == candidate: return True
        self._ensure_revision(head, depth=32)
        return self._git(['merge-base', '--is-ancestor', candidate, head], check=False).returncode == 0

    def atomic_commit(self, expected_revision, changes, message, transaction_id):
        if not self.allow_write or self.repository != REPOSITORY:
            raise RepoError('repository_read_only', '该 Git 适配器只读，不能提交或推送。', 403)
        if (not isinstance(expected_revision, str) or not _SHA.fullmatch(expected_revision)
                or not isinstance(transaction_id, str) or not _TX.fullmatch(transaction_id)
                or not isinstance(changes, dict) or not 1 <= len(changes) <= 400
                or not isinstance(message, str) or not 1 <= len(message) <= 500 or '\x00' in message):
            raise RepoError('invalid_change', 'Git 提交请求格式不正确。')
        total = 0
        for path, content in changes.items():
            if not _write_path(path): raise RepoError('path_denied', 'Git 写入路径不在题库允许范围。', 403)
            if content is not None:
                if not isinstance(content, str) or len(content.encode()) > MAX_FILE_BYTES: raise RepoError('file_limit', 'Git 修改文件过大。', 413)
                total += len(content.encode())
        if total > 8_000_000: raise RepoError('file_limit', 'Git 修改总量过大。', 413)
        digest = hashlib.sha256(json.dumps([expected_revision, changes], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        with self._lock:
            saved = self._transactions.get(transaction_id)
            if saved:
                if saved['digest'] != digest: raise RepoError('idempotency_conflict', '同一请求标识不能用于不同 Git 修改。', 409)
                if saved['status'] == 'done': return saved['candidate']
                try:
                    if self._contains(self.head(), saved['candidate']):
                        saved['status'] = 'done'; self._save_transactions(); return saved['candidate']
                except RepoError: pass
                raise RepoError('commit_uncertain', '上次 Git 推送结果仍待核实，已阻止重复推送。', 409)
            if self.head() != expected_revision: raise RepoError('conflict', 'Git 题库已被其他编辑更新，请合并后重新预览。', 409)
            if len(self._transactions) >= 1000:
                for old in list(self._transactions):
                    if self._transactions[old]['status'] == 'done': del self._transactions[old]; break
                else: raise RepoError('commit_uncertain', '待核实提交过多，请管理员先核实，不再创建新提交。', 409)
            self._ensure_revision(expected_revision)
            before = self.tree(expected_revision)
            with tempfile.TemporaryDirectory(prefix='study-index-', dir=self._root) as temp:
                index_env = {'GIT_INDEX_FILE': str(Path(temp) / 'index')}
                self._git(['read-tree', expected_revision], extra_env=index_env)
                records = []
                for path, content in sorted(changes.items()):
                    existing = before.get(path)
                    if existing and existing['mode'] not in ('100644', '100755'): raise RepoError('path_denied', '不能覆盖 Git 符号链接或非普通文件。', 403)
                    if content is None:
                        if not existing: raise RepoError('path_denied', '不能删除不存在的 Git 文件。', 403)
                        mode, sha = '0', '0' * 40
                    else:
                        mode = existing['mode'] if existing else '100644'
                        sha = self._git(['hash-object', '-w', '--stdin'], input=content.encode(), limit=100).stdout.decode().strip()
                        if not _SHA.fullmatch(sha): raise RepoError('git_invalid', 'Git 文件对象未通过核验。', 502)
                    records.append((mode + ' ' + sha + '\t' + path).encode() + b'\0')
                self._git(['update-index', '-z', '--index-info'], input=b''.join(records), extra_env=index_env)
                tree = self._git(['write-tree'], extra_env=index_env, limit=100).stdout.decode().strip()
                candidate = self._git(['commit-tree', tree, '-p', expected_revision], input=(message + '\n').encode(), limit=100).stdout.decode().strip()
                if not _SHA.fullmatch(candidate): raise RepoError('git_invalid', 'Git 提交对象未通过核验。', 502)
            self._transactions[transaction_id] = {'candidate': candidate, 'expected': expected_revision, 'digest': digest, 'status': 'pending'}
            self._save_transactions()  # Record candidate before the sole possible ref update.
            try:
                result = self._git(['push', '--porcelain', self.remote, candidate + ':refs/heads/main'], check=False, limit=262144)
            except RepoError:
                result = None
            if result is not None and result.returncode == 0:
                self._transactions[transaction_id]['status'] = 'done'; self._save_transactions(); return candidate
            try:
                if self._contains(self.head(), candidate):
                    self._transactions[transaction_id]['status'] = 'done'; self._save_transactions(); return candidate
            except RepoError: pass
            if result is not None and result.returncode != 0 and any(line.startswith(b'!\t') for line in result.stdout.splitlines()):
                del self._transactions[transaction_id]; self._save_transactions()
                raise RepoError('github_forbidden', 'Git 推送被拒绝；可能为分支冲突、保护规则或缺少写权限，不会切换凭据或强推。', 409)
            raise RepoError('commit_uncertain', 'Git 推送结果尚未核实，已阻止重复写入；请刷新核对。', 409)
