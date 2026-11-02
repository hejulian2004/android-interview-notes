"""Fixed-repository GitHub storage and bounded, reviewable study-note edits.

No authentication material is discovered here. The deployment supplies a token provider.
Remote Python/JS files are never executed; generation uses the trusted bundled generator.
"""
from __future__ import annotations
import base64
import copy
import difflib
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import secrets
import tempfile
import threading
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

REPOSITORY = 'hejulian2004/android-interview-notes'
MAX_FILE_BYTES = 1_500_000
MAX_TOTAL_BYTES = 8_000_000
READING_GUIDES = re.compile(r'(sdk-source-deep-dive|quic-source-deep-dive|ai-code-takeover-workbook)\.md$', re.I)
STATE_PATH = 'data/web-editor-state.json'

class RepoError(Exception):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def git_sha(text):
    raw = text.encode('utf-8') if isinstance(text, str) else text
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def valid_path(path):
    return (isinstance(path, str) and 0 < len(path) < 800 and '\\' not in path and '\x00' not in path
            and not path.startswith('/') and all(p not in ('', '.', '..') for p in path.split('/')))


def compatible_path(path):
    return valid_path(path) and bool(re.fullmatch(r'docs/(?:[^/]+/)*[^/]+\.md', path, re.I)
        or re.fullmatch(r'(questions|supplements)/(?:[^/]+/)*[QE]\d+[-·][^/]+\.md', path, re.I))


def _headings(text):
    result, offset, fence = [], 0, None
    for line in text.splitlines(keepends=True):
        value = line.rstrip('\r\n')
        mark = re.match(r'^ {0,3}(`{3,}|~{3,})', value)
        if mark:
            token = mark[1]
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1]:
                fence = None
        elif fence is None:
            match = re.match(r'^(#{1,6})\s+(.+?)\s*#*$', value)
            if match:
                result.append({'level': len(match[1]), 'text': match[2], 'start': offset, 'end': offset + len(value)})
        offset += len(line)
    return result


def _anchor_start(text, start):
    before = text[:start]
    anchor = re.search(r'(?:\n|^)[ \t]*<a\s+(?:id|name)=["\'][^"\']+["\']\s*>\s*</a>[ \t]*\n\s*$', before)
    return anchor.start() + (1 if before[anchor.start():].startswith('\n') else 0) if anchor else start


def _context(text, hs, heading=None):
    first_h2 = next((h for h in hs if h['level'] == 2), None)
    intro = text[:first_h2['start'] if first_h2 else min(len(text), 5000)].strip()
    facts = next((h for h in hs if h['text'] == '事实标签'), None)
    if facts:
        after = next((h for h in hs if h['start'] > facts['start'] and h['level'] <= facts['level']), None)
        intro += '\n\n' + text[facts['start']:after['start'] if after else len(text)].strip()
    if heading:
        parent = next((h for h in reversed(hs) if h['start'] < heading['start'] and h['level'] == 2), None)
        first_child = next((h for h in hs if parent and h['start'] > parent['start'] and h['level'] <= 3), None)
        section = text[parent['end']:first_child['start'] if first_child else heading['start']].strip() if parent else ''
        if section:
            intro += '\n\n' + section
    return intro


def _context_text(text):
    return re.sub(r'<a\s+(?:id|name)=["\'][^"\']+["\']\s*>\s*</a>\s*', '', text).strip()


def _slug(text):
    text = re.sub(r'[`*_]', '', text).lower()
    return ''.join(c for c in text if unicodedata.category(c)[0] in 'LMN' or c in ' _-').replace(' ', '-')


def _remove_dead_toc_links(text, question, questions):
    start = _anchor_start(text, question['start'])
    anchors = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)["\']', text[start:question['start']]))
    anchors.add(_slug(next(h['text'] for h in _headings(text) if h['start'] == question['start'])))
    output, offset, fence = [], 0, None
    for line in text.splitlines(keepends=True):
        original_length = len(line)
        mark = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if mark:
            token = mark[1]
            if fence is None: fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1]: fence = None
        inside_question = any(q['start'] <= offset < q['end'] for q in questions.values() if q['path'] == question['path'])
        if fence is None and not inside_question:
            def remove(match):
                return match[1] + '（已删除）' if match[2] in anchors else match[0]
            line = re.sub(r'\[([^\]\n]+)\]\(#([^)\s]+)\)', remove, line)
        output.append(line)
        offset += original_length
    return ''.join(output)


def parse_questions(files):
    """Mirror the production parser's heading/fence boundaries; offsets are source offsets."""
    result = {}
    for path, entry in sorted(files.items()):
        if not compatible_path(path):
            continue
        text = entry['content'] if isinstance(entry, dict) else entry
        hs = _headings(text)
        if path.startswith(('questions/', 'supplements/')):
            h = next((h for h in hs if h['level'] == 1), None)
            m = re.match(r'^([QE]\d+)\s*[·.｜:]?\s*(.+)$', h['text']) if h else None
            if m:
                qid = path + '#' + m[1].lower()
                result[qid] = dict(questionId=qid, path=path, number=m[1], title=m[2],
                    answerMarkdown=text[h['end']:].strip(), start=h['start'], headingEnd=h['end'], end=len(text),
                    sourceKind='generated', contextMarkdown=text[h['end']:next((x['start'] for x in hs if x['text'] == '参考回答提纲'), h['end'])].strip())
            continue
        if READING_GUIDES.search(path):
            continue
        for i, h in enumerate(hs):
            if h['level'] != 3:
                continue
            m = re.match(r'^([A-Z]{1,3}\d{1,4})(?:[.．｜:：·]\s*|\s+)(.+)$', h['text'])
            if not m:
                continue
            next_h = next((n for n in hs[i + 1:] if n['level'] <= 3), None)
            boundary = next_h['start'] if next_h else len(text)
            end = _anchor_start(text, boundary) if next_h else boundary
            answer = text[h['end']:end].strip()
            if len(answer) < 10:
                continue
            qid = path + '#' + m[1].lower()
            if qid in result:
                raise RepoError('invalid_catalog', '同一文档存在重复题号，不能安全编辑。', 422)
            result[qid] = dict(questionId=qid, path=path, number=m[1], title=m[2], answerMarkdown=answer,
                start=h['start'], headingEnd=h['end'], end=end, sourceKind='guide', contextMarkdown=_context(text, hs, h))
    return result


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class GitHubAdapter:
    """Fixed HTTPS host/repository. Tokens never leave api.github.com or enter messages."""
    repository = REPOSITORY
    def __init__(self, token_provider, repository=REPOSITORY, timeout=15):
        if repository != REPOSITORY:
            raise RepoError('repository_denied', '当前服务只授权访问既有题库仓库。', 403)
        self.token_provider = token_provider
        self.timeout = timeout
        self._opener = build_opener(ProxyHandler({}), _NoRedirect())
        self._commit_candidates = {}

    def _request(self, method, suffix, payload=None):
        if not suffix.startswith('/') or '\r' in suffix or '\n' in suffix:
            raise RepoError('invalid_request', '无效 GitHub 请求。')
        token = self.token_provider()
        if not isinstance(token, str) or not token or '\n' in token or '\r' in token:
            raise RepoError('github_unconfigured', '服务器尚未配置 GitHub 仓库凭据。', 503)
        headers = {'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer ' + token,
                   'User-Agent': 'android-study-server', 'X-GitHub-Api-Version': '2022-11-28'}
        raw = json.dumps(payload).encode() if payload is not None else None
        if raw is not None:
            headers['Content-Type'] = 'application/json'
        req = Request('https://api.github.com/repos/' + REPOSITORY + suffix, data=raw, headers=headers, method=method)
        try:
            with self._opener.open(req, timeout=self.timeout) as response:
                data = response.read(MAX_TOTAL_BYTES + 1)
                if len(data) > MAX_TOTAL_BYTES:
                    raise RepoError('github_limit', 'GitHub 响应超过安全大小限制。', 502)
                return json.loads(data)
        except HTTPError as exc:
            if exc.code in (409, 422):
                raise RepoError('conflict', 'GitHub 分支已变化或不允许此更新，请刷新并重新检查差异。', 409) from None
            if exc.code in (401, 403):
                raise RepoError('github_forbidden', 'GitHub 凭据权限不足、分支受保护或请求受限；未绕过仓库规则。', 502) from None
            raise RepoError('github_failure', 'GitHub 请求失败，请保留草稿后重试。', 502) from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise RepoError('github_unavailable', 'GitHub 暂不可用，请保留草稿。', 503) from None

    def head(self):
        sha = self._request('GET', '/git/ref/heads/main')['object']['sha']
        if not re.fullmatch(r'[a-f0-9]{40}', sha):
            raise RepoError('github_invalid', 'GitHub 返回无效提交版本。', 502)
        return sha

    def tree(self, revision):
        if not re.fullmatch(r'[a-f0-9]{40}', revision):
            raise RepoError('invalid_revision', '源码必须固定到完整提交 SHA。')
        value = self._request('GET', '/git/trees/' + revision + '?recursive=1')
        if value.get('truncated') or len(value.get('tree', [])) > 12000:
            raise RepoError('github_limit', '仓库树不完整或过大，未使用不完整索引。', 502)
        return {f['path']: {'sha': f['sha'], 'mode': f['mode'], 'size': f.get('size', 0)}
                for f in value['tree'] if f['type'] == 'blob' and valid_path(f['path'])}

    def read(self, revision, path, entry=None):
        entry = entry or self.tree(revision).get(path)
        if not entry or entry.get('mode') not in ('100644', '100755'):
            raise RepoError('path_denied', '目标不是允许读取的普通文本文件。', 403)
        if entry.get('size', 0) > MAX_FILE_BYTES:
            raise RepoError('file_limit', '文件过大，不能在此读取。', 413)
        value = self._request('GET', '/git/blobs/' + entry['sha'])
        try:
            if value.get('encoding') != 'base64':
                raise ValueError()
            raw = base64.b64decode(value['content'])
            if len(raw) > MAX_FILE_BYTES or b'\0' in raw or git_sha(raw) != entry['sha']:
                raise ValueError()
            return raw.decode('utf-8')
        except (ValueError, KeyError, UnicodeError):
            raise RepoError('file_invalid', '目标不是有效的受限 UTF-8 文本。', 422) from None

    def atomic_commit(self, expected_revision, changes, message, transaction_id):
        # A retry reuses the exact candidate commit, never creates a second commit.
        if transaction_id in self._commit_candidates:
            candidate = self._commit_candidates[transaction_id]
            if self._contains_commit(self.head(), candidate):
                self._commit_candidates.pop(transaction_id, None)
                return candidate
            raise RepoError('commit_uncertain', '上次提交结果仍待核实；不会重复写入，请先刷新核对。', 409)
        if self.head() != expected_revision:
            raise RepoError('conflict', '题库已被其他编辑更新，请刷新后合并草稿。', 409)
        base = self._request('GET', '/git/commits/' + expected_revision)
        entries = []
        for path, content in sorted(changes.items()):
            if content is None:
                entries.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': None})
            else:
                blob = self._request('POST', '/git/blobs', {'content': base64.b64encode(content.encode()).decode(), 'encoding': 'base64'})
                entries.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
        tree = self._request('POST', '/git/trees', {'base_tree': base['tree']['sha'], 'tree': entries})
        commit = self._request('POST', '/git/commits', {'message': message, 'tree': tree['sha'], 'parents': [expected_revision]})
        candidate = commit['sha']
        self._commit_candidates[transaction_id] = candidate
        try:
            self._request('PATCH', '/git/refs/heads/main', {'sha': candidate, 'force': False})
        except RepoError as exc:
            try:
                if self._contains_commit(self.head(), candidate):
                    self._commit_candidates.pop(transaction_id, None)
                    return candidate
            except RepoError:
                pass
            # Explicit rejection is known not to have updated the ref; an unavailable
            # response may have executed. Never silently retry a possible write.
            if exc.code in ('conflict', 'github_forbidden'):
                self._commit_candidates.pop(transaction_id, None)
                raise
            raise RepoError('commit_uncertain', 'GitHub 提交结果不确定，已阻止重复提交；请刷新核对。', 409) from None
        self._commit_candidates.pop(transaction_id, None)
        return candidate

    def _contains_commit(self, head, candidate):
        for _ in range(12):
            if head == candidate:
                return True
            parents = self._request('GET', '/git/commits/' + head).get('parents', [])
            if not parents:
                return False
            head = parents[0]['sha']
        return False


class MemoryAdapter:
    """Deterministic fixture transport. Never used as a production write credential."""
    repository = REPOSITORY
    def __init__(self, files):
        self._versions = {}
        self._files = dict(files)
        self._counter = 0
        self.fail = False
        self.commits = []
        self._save()

    def _save(self):
        self._counter += 1
        self._head = hashlib.sha1((json.dumps(self._files, sort_keys=True) + str(self._counter)).encode()).hexdigest()
        self._versions[self._head] = dict(self._files)

    def head(self):
        if self.fail:
            raise RepoError('github_unavailable', '模拟 GitHub 不可用。', 503)
        return self._head

    def tree(self, revision):
        if revision not in self._versions:
            raise RepoError('invalid_revision', '未知提交版本。', 404)
        return {p: {'sha': git_sha(c), 'mode': '100644', 'size': len(c.encode())} for p, c in self._versions[revision].items()}

    def read(self, revision, path, entry=None):
        try:
            return self._versions[revision][path]
        except KeyError:
            raise RepoError('not_found', '文件不存在。', 404) from None

    def atomic_commit(self, expected_revision, changes, message, transaction_id):
        if self.fail:
            raise RepoError('github_unavailable', '模拟 GitHub 不可用。', 503)
        if self._head != expected_revision:
            raise RepoError('conflict', '模拟并发编辑冲突。', 409)
        for path, content in changes.items():
            if content is None:
                self._files.pop(path, None)
            else:
                self._files[path] = content
        self._save()
        self.commits.append({'sha': self._head, 'changes': dict(changes), 'transactionId': transaction_id})
        return self._head


class ContentRepository:
    def __init__(self, adapter, clock=time.time, draft_ttl=900, cache_ttl=1800, generator_path=None):
        if adapter.repository != REPOSITORY:
            raise RepoError('repository_denied', '只允许已注册的题库仓库。', 403)
        self.adapter, self.clock = adapter, clock
        self.draft_ttl, self.cache_ttl = draft_ttl, cache_ttl
        self.generator_path = Path(generator_path) if generator_path else Path(__file__).resolve().parents[2] / 'scripts' / 'build.py'
        self._cache, self._tree_cache, self._text_cache = None, {}, {}
        self._drafts, self._results = {}, {}
        self._source_export = False
        self._lock = threading.RLock()
        self._io_lock = threading.Lock()

    def _tree(self, revision):
        # Only dictionary operations share this lock. Holding it while fetching
        # would serialize catalog workers (or deadlock if _lock were reused).
        with self._io_lock:
            cached = self._tree_cache.get(revision)
        if cached is not None:
            return cached
        tree = self.adapter.tree(revision)
        with self._io_lock:
            self._tree_cache[revision] = tree
            while len(self._tree_cache) > 8:
                self._tree_cache.pop(next(iter(self._tree_cache)))
        # Return the local immutable tree even if another request evicts its key.
        return tree

    def _read(self, revision, path):
        tree = self._tree(revision)
        if path not in tree or tree[path]['mode'] not in ('100644', '100755'):
            raise RepoError('path_denied', '不允许读取符号链接或未注册路径。', 403)
        entry = tree[path]
        key = (path, entry['sha'])
        with self._io_lock:
            cached = self._text_cache.get(key)
        if cached is not None:
            return cached
        text = self.adapter.read(revision, path, entry)
        if len(text.encode()) > MAX_FILE_BYTES or '\0' in text or git_sha(text) != entry['sha']:
            raise RepoError('file_invalid', '文件内容未通过大小或完整性校验。', 422)
        with self._io_lock:
            self._text_cache[key] = text
            while len(self._text_cache) > 700:
                self._text_cache.pop(next(iter(self._text_cache)))
        return text

    def catalog(self, force=False):
        with self._lock:
            now = self.clock()
            if self._cache and not force and now - self._cache['checkedAt'] / 1000 < self.cache_ttl:
                return copy.deepcopy(self._cache)
            try:
                revision = self.adapter.head()
                tree = self._tree(revision)
                paths = [p for p in tree if compatible_path(p) and tree[p]['mode'] in ('100644', '100755')]
                if not paths or len(paths) > 400:
                    raise RepoError('catalog_limit', '题库为空或超过文件数限制。', 422)
                files, total = [], 0
                pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix='study-github')
                futures = {pool.submit(self._read, revision, path): path for path in sorted(paths)}
                try:
                    for future in as_completed(futures, timeout=65):
                        path, text = futures[future], future.result()
                        total += len(text.encode())
                        if total > MAX_TOTAL_BYTES:
                            raise RepoError('catalog_limit', '题库超过大小限制。', 422)
                        files.append({'path': path, 'sha': tree[path]['sha'], 'content': text})
                except FuturesTimeout:
                    raise RepoError('github_timeout', '题库刷新超时，未替换成功缓存。', 503) from None
                finally:
                    pool.shutdown(wait=False, cancel_futures=True)
                files.sort(key=lambda f: f['path'])
                if not parse_questions({f['path']: f for f in files}):
                    raise RepoError('invalid_catalog', '没有可解析的题目。', 422)
                from datetime import datetime, timezone
                self._cache = {'version': 1, 'revision': revision, 'files': files, 'checkedAt': int(now * 1000),
                    'fetchedAt': datetime.fromtimestamp(now, timezone.utc).isoformat(), 'generatedAt': None,
                    'origin': 'github', 'warning': ''}
            except RepoError:
                if not self._cache:
                    raise
                result = copy.deepcopy(self._cache)
                result.update(origin='server-cache', warning='GitHub 更新失败，当前为服务器上次成功题库；尚未确认最新版本。')
                return result
            return copy.deepcopy(self._cache)

    def _current(self, base_revision=None):
        value = self.catalog(force=True)
        if value.get('warning'):
            raise RepoError('github_unavailable', '当前无法确认 GitHub 最新版本，暂不允许写入。', 503)
        if base_revision and value['revision'] != base_revision:
            raise RepoError('conflict', '题库版本已变化，请刷新后合并；草稿没有提交。', 409)
        return value, {f['path']: f for f in value['files']}

    def editable(self, question_id):
        value, files = self._current()
        question = parse_questions(files).get(question_id)
        if not question:
            raise RepoError('not_found', '题目不存在或已被删除。', 404)
        result = {k: v for k, v in question.items() if k not in ('start', 'end', 'headingEnd')}
        if question['sourceKind'] == 'generated':
            records = self._json(value['revision'], 'data/questions.json')
            row = next((r for r in records if r['id'] == question['number']), None)
            if row is None:
                raise RepoError('invalid_source', '生成题目缺少规范数据，不能安全编辑。', 422)
            result['answerMarkdown'] = row['answer']
            result['contextMarkdown'] += '\n\n此处编辑规范数据中的参考回答；证据、易错点、追问和技术边界会保留。\n\n## 易错点（只读）\n' + row['pitfall'] + '\n\n## 延伸追问（只读）\n' + row['followup'] + '\n\n## 技术边界（只读）\n' + row['answer_provenance']
        result.update(baseRevision=value['revision'], blobSha=files[question['path']]['sha'])
        return result

    def _json(self, revision, path):
        try:
            return json.loads(self._read(revision, path))
        except (ValueError, TypeError):
            raise RepoError('invalid_source', '规范数据格式不正确。', 422) from None

    def _state(self, revision, questions):
        try:
            state = self._json(revision, STATE_PATH) if STATE_PATH in self._tree(revision) else {'version': 1, 'used': {}}
            if state.get('version') != 1 or not isinstance(state.get('used'), dict):
                raise ValueError()
            for q in questions.values():
                values = state['used'].setdefault(q['path'], [])
                if not isinstance(values, list) or any(not isinstance(x, str) for x in values):
                    raise ValueError()
                if q['number'] not in values:
                    values.append(q['number'])
            return state
        except (ValueError, TypeError, AttributeError):
            raise RepoError('invalid_source', '题号保留记录损坏，不能分配或删除题目。', 422) from None

    def preview(self, change):
        with self._lock:
            if not isinstance(change, dict) or change.get('operation') not in ('update', 'create', 'delete'):
                raise RepoError('invalid_change', '请选择有效的增、改或删除操作。')
            base_revision = change.get('baseRevision')
            if not isinstance(base_revision, str) or not re.fullmatch('[a-f0-9]{40}', base_revision):
                raise RepoError('base_required', '修改必须携带读取时的完整提交版本。', 409)
            catalog, files = self._current(base_revision)
            before = parse_questions(files)
            operation = change['operation']
            requested_id = change.get('questionId')
            if requested_id is not None and (not isinstance(requested_id, str) or len(requested_id) > 1000):
                raise RepoError('invalid_question', '题目标识格式不正确。')
            question = before.get(requested_id)
            if operation != 'create' and not question:
                raise RepoError('not_found', '题目不存在或已删除。', 404)
            if question and change.get('blobSha') != files[question['path']]['sha']:
                raise RepoError('conflict', '原文件 SHA 已变化或缺失，请重新读取题目。', 409)
            title = change.get('title', question['title'] if question else '')
            answer = change.get('answerMarkdown', question['answerMarkdown'] if question else '')
            if operation != 'delete':
                if not isinstance(title, str) or not title.strip() or len(title) > 240 or '\n' in title or '\r' in title:
                    raise RepoError('invalid_title', '题目标题应为 1–240 字的单行文字。')
                if not isinstance(answer, str) or len(answer.strip()) < 10 or len(answer.encode()) > 150_000:
                    raise RepoError('invalid_answer', '答案至少 10 字，且不超过 150KB。')
                title, answer = title.strip(), answer.strip()
            changes, new_id = {}, question['questionId'] if question else None
            state = None
            if operation in ('create', 'delete'):
                state = self._state(base_revision, before)
            if question and question['sourceKind'] == 'generated':
                changes = self._edit_generated(base_revision, question, operation, title, answer)
            elif operation == 'create':
                path = change.get('documentPath')
                if not isinstance(path, str) or not path.startswith('docs/') or path not in files or READING_GUIDES.search(path):
                    raise RepoError('path_denied', '新增题目请选择现有的编号问答导读；不能创建任意文件。', 403)
                siblings = [q for q in before.values() if q['path'] == path]
                if not siblings:
                    raise RepoError('invalid_document', '所选文档没有兼容的编号题目。')
                if any(h['level'] <= 3 for h in _headings(answer)):
                    raise RepoError('invalid_answer', '答案内的小标题请使用四级及以下；代码围栏中的标题不受影响。')
                used = state['used'].setdefault(path, [])
                prefixes = [re.sub(r'\d+$', '', q['number']) for q in siblings]
                prefix = max(set(prefixes), key=prefixes.count)
                numbers = [int(n[len(prefix):]) for n in used if re.fullmatch(re.escape(prefix) + r'\d+', n)]
                number = prefix + str(max(numbers, default=0) + 1).zfill(2)
                used.append(number)
                new_id = path + '#' + number.lower()
                changes[path] = files[path]['content'].rstrip() + '\n\n### ' + number + ' ' + title + '\n\n' + answer + '\n'
            else:
                path, text = question['path'], files[question['path']]['content']
                if operation == 'delete':
                    cleaned = _remove_dead_toc_links(text, question, before)
                    # TOC replacements change earlier offsets; reparse exact target.
                    current_q = parse_questions({path: cleaned})[question['questionId']]
                    start = _anchor_start(cleaned, current_q['start'])
                    changes[path] = cleaned[:start] + cleaned[current_q['end']:]
                else:
                    if any(h['level'] <= 3 for h in _headings(answer)):
                        raise RepoError('invalid_answer', '答案内的小标题请使用四级及以下；代码围栏中的标题不受影响。')
                    if title == question['title'] and answer == question['answerMarkdown']:
                        raise RepoError('no_changes', '内容没有变化，无需创建 GitHub 提交。')
                    preserved_anchor = ''
                    if title != question['title'] and _anchor_start(text, question['start']) == question['start']:
                        heading = next(h['text'] for h in _headings(text) if h['start'] == question['start'])
                        preserved_anchor = '<a id="' + _slug(heading) + '"></a>\n'
                    changes[path] = text[:question['start']] + preserved_anchor + '### ' + question['number'] + ' ' + title + '\n\n' + answer + '\n\n' + text[question['end']:]
            if state is not None:
                changes[STATE_PATH] = json.dumps(state, ensure_ascii=False, indent=2) + '\n'
            changes = {p: c for p, c in changes.items() if c != (self._read(base_revision, p) if p in self._tree(base_revision) else None)}
            if not changes:
                raise RepoError('no_changes', '内容没有变化，无需创建 GitHub 提交。')
            self._validate_change(files, before, changes, operation, new_id)
            diff = ''.join(''.join(difflib.unified_diff(
                (self._read(base_revision, p) if p in self._tree(base_revision) else '').splitlines(True),
                (c or '').splitlines(True), fromfile='a/' + p, tofile='b/' + p)) for p, c in sorted(changes.items()))
            if len(diff.encode()) > 1_500_000:
                raise RepoError('diff_limit', '修改差异过大，请分批操作。', 413)
            draft_id = secrets.token_urlsafe(24)
            now = self.clock()
            self._drafts = {k: d for k, d in self._drafts.items() if now < d['expiresAt']}
            if len(self._drafts) >= 60:
                raise RepoError('draft_limit', '服务端待确认草稿过多，请等待旧草稿过期。', 429)
            draft = {'draftId': draft_id, 'baseRevision': base_revision, 'questionId': new_id, 'operation': operation,
                'changes': changes, 'diff': diff, 'expiresAt': now + self.draft_ttl, 'summary': ('新增' if operation == 'create' else '删除' if operation == 'delete' else '修改') + '题目 ' + (question['number'] if question else new_id.split('#')[-1])}
            self._drafts[draft_id] = draft
            return {k: v for k, v in draft.items() if k not in ('changes', 'operation')} | {'changedPaths': sorted(changes)}

    def _generator(self):
        # This path is the deployed application's trusted generator, never a fetched
        # source path. No exec/shell/subprocess is exposed to user or model input.
        spec = importlib.util.spec_from_file_location('_trusted_study_generator', self.generator_path)
        if not spec or not spec.loader:
            raise RepoError('generator_unavailable', '服务器未打包题库生成器。', 503)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _edit_generated(self, revision, question, operation, title, answer):
        source_paths = ('data/questions.json', 'data/sources.json', 'data/references.json')
        source = {p: self._json(revision, p) for p in source_paths}
        records = source['data/questions.json']
        row = next((r for r in records if r['id'] == question['number']), None)
        if row is None:
            raise RepoError('invalid_source', '题目规范数据不存在。', 422)
        # The backend ships reviewed generator code. A newer remote template must
        # never be replaced by this older deployed version, even with a fresh HEAD.
        tree = self._tree(revision)
        try:
            trusted_generator_sha = git_sha(self.generator_path.read_bytes())
        except OSError:
            raise RepoError('generator_unavailable', '服务器未打包可信题库生成器。', 503) from None
        remote_generator = tree.get('scripts/build.py')
        if not remote_generator or remote_generator.get('mode') not in ('100644', '100755') or remote_generator.get('sha') != trusted_generator_sha:
            raise RepoError('generator_version_conflict', '仓库生成器与服务器版本不一致，已阻止覆盖更新；请先审查并更新服务器程序。', 409)
        generator = self._generator()
        baseline = self._generate_source(generator, source)
        # SHA comparison covers exact UTF-8 bytes, not just parsed questions. It
        # protects README, evidence, indexes, and manually patched generated files.
        for path, content in baseline.items():
            current = tree.get(path)
            if not self._generated_write_path(path):
                raise RepoError('generator_path_denied', '生成器基线包含未允许的文件路径。', 422)
            if not current or current.get('mode') not in ('100644', '100755') or current.get('sha') != git_sha(content):
                raise RepoError('generator_version_conflict', '仓库生成产物与规范数据基线不一致，已保留远端修改；请先在仓库解决差异。', 409)
        generated_questions = {path for path in baseline if path.startswith(('questions/', 'supplements/')) and compatible_path(path)}
        tracked_questions = {path for path in tree if path.startswith(('questions/', 'supplements/')) and compatible_path(path)}
        if tracked_questions != generated_questions:
            raise RepoError('generator_version_conflict', '仓库生成题目清单与规范数据不一致，已阻止不完整更新。', 409)
        previous_paths = {generator.question_path(r) for r in records}
        if operation == 'delete':
            records.remove(row)
            remaining_sources = {e['source_id'] for r in records for e in r['evidence']}
            lost = [s['id'] for s in source['data/sources.json'] if s['status'] == 'admitted' and s['id'] not in remaining_sources]
            if lost:
                raise RepoError('source_integrity', '删除会使正式来源失去所有题目。请先在仓库调整来源归属，本次未写入。', 422)
        else:
            row['title'], row['answer'], row['source_path'] = title, answer, question['path']
        generated = self._generate_source(generator, source)
        if operation != 'delete' and generator.question_path(row) != question['path']:
            raise RepoError('generator_incompatible', '生成器尚未支持稳定文件路径，已阻止导致学习进度丢失的修改。', 503)
        changes = {'data/questions.json': json.dumps(records, ensure_ascii=False, indent=2) + '\n'}
        # collect_files is the shipped audited generator, and only these generated
        # destinations are eligible for GitHub writes.
        for p, content in generated.items():
            if not self._generated_write_path(p):
                raise RepoError('generator_path_denied', '生成器尝试写入不允许的文件路径。', 422)
            changes[p] = content
        current_paths = {generator.question_path(r) for r in records}
        for path in previous_paths - current_paths:
            changes[path] = None
        return changes

    @staticmethod
    def _generate_source(generator, source):
        with tempfile.TemporaryDirectory(prefix='study-generate-') as temp:
            root = Path(temp)
            (root / 'data').mkdir()
            for path, value in source.items():
                (root / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            generated, _stats = generator.collect_files(root)
            return generated

    @staticmethod
    def _generated_write_path(path):
        return valid_path(path) and (path in ('README.md', 'METHODOLOGY.md', 'data/stats.json', 'data/generated-files.json', 'references/README.md')
            or path.startswith(('questions/', 'supplements/', 'sources/', 'indexes/')) and path.endswith('.md'))

    def _validate_change(self, files, before, changes, operation, qid):
        after_files = {p: dict(f) for p, f in files.items()}
        for path, content in changes.items():
            if compatible_path(path):
                if content is None:
                    after_files.pop(path, None)
                else:
                    after_files[path] = {'content': content}
        after = parse_questions(after_files)
        if not after:
            raise RepoError('empty_catalog', '不能删除最后一道题目；题库必须保留至少一道可解析问题。', 422)
        expected = set(before)
        if operation == 'create':
            expected.add(qid)
        elif operation == 'delete':
            expected.remove(qid)
        if set(after) != expected:
            raise RepoError('unsafe_edit', '修改会改变其他题号或 Markdown 边界，已阻止提交。', 422)
        for old_id, question in before.items():
            if old_id != qid and (after[old_id]['answerMarkdown'] != question['answerMarkdown'] or after[old_id]['title'] != question['title'] or (operation != 'delete' and _context_text(after[old_id]['contextMarkdown']) != _context_text(question['contextMarkdown']))):
                raise RepoError('unsafe_edit', '修改触及其他题目的答案，已阻止提交。', 422)
        if qid in after and len(after[qid]['answerMarkdown']) < 10:
            raise RepoError('invalid_answer', '修改后答案不完整。', 422)

    def mark_private_proposal(self, draft_id, disclosure):
        """Internal trusted call only; intentionally no HTTP endpoint exposes this."""
        with self._lock:
            if not isinstance(draft_id, str) or not isinstance(disclosure, dict):
                raise RepoError('publication_disclosure', '私有源码发布说明格式无效。')
            name, revision = disclosure.get('repository'), disclosure.get('revision')
            if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', name) or not isinstance(revision, str) or not re.fullmatch(r'[a-f0-9]{40}', revision) or disclosure.get('private') is not True:
                raise RepoError('publication_disclosure', '私有源码发布说明必须包含已核验仓库和固定版本。')
            draft = self._drafts.get(draft_id)
            if not draft or self.clock() >= draft['expiresAt'] or draft.get('committed'):
                raise RepoError('draft_expired', '草稿已过期或已提交，请重新生成并核对。', 410)
            safe = {key: copy.deepcopy(disclosure[key]) for key in ('repository', 'revision', 'private', 'providerConfigVersion', 'pathPrefixes') if key in disclosure}
            draft['requiresPublicConfirmation'] = True
            draft['publicationDisclosure'] = safe
            return {key: copy.deepcopy(value) for key, value in draft.items() if key not in ('changes', 'operation', 'pending')} | {'changedPaths': sorted(draft['changes'])}

    def commit(self, draft_id, idempotency_key, actor='admin', confirm_public_publication=False):
        with self._lock:
            if not isinstance(draft_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{20,80}', draft_id):
                raise RepoError('invalid_draft', '服务器草稿标识格式不正确。')
            if not isinstance(idempotency_key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,120}', idempotency_key):
                raise RepoError('idempotency_required', '提交需要有效的唯一请求标识。')
            if idempotency_key in self._results:
                saved = self._results[idempotency_key]
                if saved['draftId'] != draft_id:
                    raise RepoError('idempotency_conflict', '此请求标识已用于另一份修改。', 409)
                return copy.deepcopy(saved['result'])
            draft = self._drafts.get(draft_id)
            if not draft or self.clock() >= draft['expiresAt']:
                raise RepoError('draft_expired', '服务器草稿已过期，请保留本地内容并重新预览。', 410)
            if draft.get('committed'):
                return copy.deepcopy(draft['committed'])
            if draft.get('requiresPublicConfirmation') and confirm_public_publication is not True:
                raise RepoError('public_publication_confirmation', '此建议涉及私有源码；发布到公开题库前必须另行明确确认。', 403)
            # An uncertain ref update must be verified by the adapter before checking
            # old HEAD: the possible successful write itself changed that HEAD.
            if not draft.get('pending'):
                self._current(draft['baseRevision'])
            try:
                commit = self.adapter.atomic_commit(draft['baseRevision'], draft['changes'],
                    'study: ' + draft['summary'], draft_id)
            except RepoError as error:
                if error.code == 'commit_uncertain':
                    draft['pending'] = True
                raise
            if not re.fullmatch(r'[a-f0-9]{40}', str(commit)):
                raise RepoError('commit_uncertain', 'GitHub 提交版本未核实，不能报告保存成功。', 502)
            result = {'commit': commit, 'questionId': draft['questionId'], 'deleted': draft['operation'] == 'delete',
                'message': '已同步 GitHub。', 'commitUrl': f'https://github.com/{REPOSITORY}/commit/{commit}'}
            self._results[idempotency_key] = {'draftId': draft_id, 'result': result}
            while len(self._results) > 1000:
                self._results.pop(next(iter(self._results)))
            draft['committed'] = result
            self._cache = None
            return copy.deepcopy(result)

    def source_repos(self):
        value = self.catalog()
        return {'repositories': [{'repository': REPOSITORY, 'private': False, 'allowModelExport': self._source_export, 'revision': value['revision']}]}

    def authorize_source(self, repository, allow_model_export):
        if repository != REPOSITORY or type(allow_model_export) is not bool:
            raise RepoError('repository_denied', '当前仅注册公开题库仓库；新增或私有仓库需明确后端配置与授权。', 403)
        self._source_export = allow_model_export
        return self.source_repos()

    @staticmethod
    def _source_path(path):
        if not valid_path(path):
            return False
        parts = PurePosixPath(path).parts
        lowered = path.lower()
        if any(part.startswith('.') or part.lower() in ('node_modules', 'dist', '__pycache__', 'logs', 'backups', 'private') for part in parts):
            return False
        if any(word in lowered for word in ('credential', 'secret', 'private_key', 'id_rsa', 'id_ed25519', 'token', '.env')):
            return False
        if not path.endswith(('.md', '.py', '.js', '.mjs', '.ts', '.tsx', '.jsx', '.json', '.html', '.css', '.java', '.kt', '.rs', '.dart', '.xml', '.toml', '.yaml', '.yml')):
            return False
        return path in ('README.md', 'METHODOLOGY.md') or path.startswith(('docs/', 'questions/', 'supplements/', 'scripts/', 'tests/', 'web/src/', 'web/engine/', 'data/'))

    def _source_context(self, repository, revision):
        if repository not in (None, REPOSITORY):
            raise RepoError('repository_denied', '源码仓库未被服务器明确注册，未发起读取。', 403)
        if revision is None:
            revision = self.catalog()['revision']
        if not isinstance(revision, str) or not re.fullmatch(r'[a-f0-9]{40}', revision):
            raise RepoError('invalid_revision', '源码引用必须固定到完整提交 SHA。')
        return revision, self._tree(revision)

    def read_source(self, path, start_line=1, end_line=120, repository=None, revision=None):
        revision, tree = self._source_context(repository, revision)
        if not self._source_path(path) or path not in tree or tree[path]['mode'] not in ('100644', '100755'):
            raise RepoError('path_denied', '路径不在源码只读允许范围内。', 403)
        if type(start_line) is not int or type(end_line) is not int or start_line < 1 or end_line < start_line or end_line - start_line >= 200:
            raise RepoError('line_limit', '每次最多读取 200 行，且行号必须有效。')
        text = self._read(revision, path)
        lines = text.splitlines()
        if start_line > max(1, len(lines)):
            raise RepoError('line_limit', '起始行超出文件范围。')
        end_line = min(end_line, len(lines))
        content = '\n'.join(lines[start_line - 1:end_line])
        if len(content.encode()) > 40_000:
            raise RepoError('source_limit', '选定代码段过大，请缩小行数范围。', 413)
        return {'repository': REPOSITORY, 'revision': revision, 'path': path, 'startLine': start_line, 'endLine': end_line,
            'text': content, 'sourceUrl': f'https://github.com/{REPOSITORY}/blob/{revision}/{quote(path, safe="/")}#L{start_line}-L{end_line}',
            'content': content, 'url': f'https://github.com/{REPOSITORY}/blob/{revision}/{quote(path, safe="/")}#L{start_line}-L{end_line}',
            'allowModelExport': self._source_export}

    def search_source(self, query, repository=None, revision=None):
        if not isinstance(query, str) or not 2 <= len(query.strip()) <= 160:
            raise RepoError('invalid_query', '源码搜索词应为 2–160 字。')
        revision, tree = self._source_context(repository, revision)
        query = query.strip().casefold()
        results, scanned, total = [], 0, 0
        candidates = [p for p in sorted(tree) if self._source_path(p) and tree[p]['mode'] in ('100644', '100755') and tree[p].get('size', 0) <= 300_000]
        deadline = time.monotonic() + 20
        for path in candidates[:180]:
            if time.monotonic() > deadline:
                break
            text = self._read(revision, path)
            total += len(text.encode())
            if total > 4_000_000:
                break
            scanned += 1
            for n, line in enumerate(text.splitlines(), 1):
                if query in line.casefold():
                    results.append({'repository': REPOSITORY, 'revision': revision, 'path': path, 'startLine': n, 'endLine': n,
                        'text': line[:700], 'sourceUrl': f'https://github.com/{REPOSITORY}/blob/{revision}/{quote(path, safe="/")}#L{n}',
                        'content': line[:700], 'url': f'https://github.com/{REPOSITORY}/blob/{revision}/{quote(path, safe="/")}#L{n}'})
                    if len(results) >= 30:
                        break
            if len(results) >= 30:
                break
        return {'repository': REPOSITORY, 'revision': revision, 'results': results, 'filesScanned': scanned,
            'truncated': scanned < len(candidates) or len(results) >= 30,
            'notice': '有界文本检索，未构建编译器语义索引；未命中不代表仓库不存在相关实现。', 'allowModelExport': self._source_export}
