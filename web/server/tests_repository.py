import copy
from concurrent.futures import ThreadPoolExecutor
import threading
import json
from pathlib import Path
import tempfile
import unittest
from .repository import ContentRepository, MemoryAdapter, GitHubAdapter, RepoError, REPOSITORY, parse_questions, git_sha

ROOT = Path(__file__).resolve().parents[2]

def actual_fixture():
    files = {}
    for base in ('docs', 'questions', 'supplements', 'data', 'indexes', 'sources', 'references'):
        for path in (ROOT / base).rglob('*'):
            if path.is_file() and path.suffix in ('.md', '.json'):
                files[path.relative_to(ROOT).as_posix()] = path.read_text()
    for path in ('README.md', 'METHODOLOGY.md', 'scripts/build.py'):
        files[path] = (ROOT / path).read_text()
    return files

SIMPLE = {'docs/sample.md': '# 示例\n\n版本边界：仅通用练习，未证明实际运行。\n\n- [第一题](#a01)\n- [第二题](#a02)\n\n## 基础\n\n<a id="a01"></a>\n### A01 第一题\n\n原始答案足够长，保留事实限制。\n\n<a id="a02"></a>\n### A02 第二题\n\n第二道题的原始答案，不能被另一题修改。\n'}

class RepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = actual_fixture()

    def setUp(self):
        self.adapter = MemoryAdapter(SIMPLE)
        self.repo = ContentRepository(self.adapter)

    def edited(self, qid='docs/sample.md#a01', **patch):
        change = self.repo.editable(qid)
        change.update(operation='update', answerMarkdown='新的参考回答，保留事实限制并说明适用条件。')
        change.update(patch)
        return self.repo.preview(change)

    def test_actual_491_questions_and_context(self):
        repo = ContentRepository(MemoryAdapter(self.actual))
        catalog = repo.catalog()
        questions = parse_questions({f['path']: f for f in catalog['files']})
        self.assertEqual(len(questions), 491)
        self.assertEqual(len([p for p in self.actual if p.startswith('docs/') and p.endswith('.md')]), 10)
        context = repo.editable('docs/android-interview-handbook.md#n01')['contextMarkdown']
        self.assertIn('事实标签', context)
        self.assertIn('不代表', context)
        self.assertEqual(len([q for q in questions.values() if q['number'].startswith('JA')]), 40)

    def test_doc_edit_preserves_neighbor_code_and_anchor(self):
        before = parse_questions(SIMPLE)
        answer = '**口述回答：** 新的答案保持代码文字。\n\n```kotlin\n// ### Z99 不是题目\nval wildcard = "*"\n```\n\n#### 追问\n\n保留适用边界。'
        preview = self.edited(answerMarkdown=answer, title='修改后的标题')
        self.assertEqual(self.adapter.commits, [])
        result = self.repo.commit(preview['draftId'], 'request_0123456789')
        after = parse_questions(self.adapter._files)
        self.assertEqual(set(before), set(after))
        self.assertEqual({k:v for k,v in before['docs/sample.md#a02'].items() if k not in ('start','end','headingEnd')}, {k:v for k,v in after['docs/sample.md#a02'].items() if k not in ('start','end','headingEnd')})
        self.assertIn('<a id="a02"></a>', self.adapter._files['docs/sample.md'])
        self.assertEqual(after['docs/sample.md#a01']['answerMarkdown'], answer)
        self.assertEqual(result['commit'], self.adapter.head())

    def test_delete_toc_is_not_broken_and_deleted_code_not_reused(self):
        draft = self.repo.preview(dict(self.repo.editable('docs/sample.md#a02'), operation='delete'))
        self.repo.commit(draft['draftId'], 'delete_0123456789')
        self.assertNotIn('](#a02)', self.adapter._files['docs/sample.md'])
        self.assertIn('第二题（已删除）', self.adapter._files['docs/sample.md'])
        current = self.repo.catalog()['revision']
        draft = self.repo.preview({'operation': 'create', 'documentPath': 'docs/sample.md', 'baseRevision': current,
            'title': '新增问题', 'answerMarkdown': '新题目包含完整回答，明确只是练习设定。'})
        self.assertEqual(draft['questionId'], 'docs/sample.md#a03')
        self.repo.commit(draft['draftId'], 'create_0123456789')
        self.assertEqual(len(parse_questions(self.adapter._files)), 2)

    def test_title_change_preserves_preexisting_generated_heading_anchor(self):
        adapter = MemoryAdapter({'docs/no-anchor.md':'# Guide\n\n- [旧标题](#a01-旧标题)\n\n## 练习\n\n### A01 旧标题\n\n参考回答完整且保留来源边界。\n\n### A02 第二题\n\n第二题不应丢失其原有的上下文。\n'})
        repo = ContentRepository(adapter)
        draft = repo.preview(dict(repo.editable('docs/no-anchor.md#a01'), operation='update', title='新标题'))
        repo.commit(draft['draftId'], 'anchor_0123456789')
        self.assertIn('<a id="a01-旧标题"></a>', adapter._files['docs/no-anchor.md'])
        self.assertIn('](#a01-旧标题)', adapter._files['docs/no-anchor.md'])

    def test_conflict_and_missing_sha_never_write(self):
        change = self.repo.editable('docs/sample.md#a01')
        with self.assertRaises(RepoError) as error:
            self.repo.preview(dict(change, operation='update', blobSha='0'*40))
        self.assertEqual(error.exception.code, 'conflict')
        draft = self.edited()
        self.adapter.atomic_commit(self.adapter.head(), {'README.md': 'concurrent change'}, 'external', 'external')
        with self.assertRaises(RepoError) as error:
            self.repo.commit(draft['draftId'], 'conflict_0123456789')
        self.assertEqual(error.exception.code, 'conflict')
        self.assertEqual(len(self.adapter.commits), 1)

    def test_duplicate_request_or_same_draft_does_not_commit_twice(self):
        draft = self.edited()
        first = self.repo.commit(draft['draftId'], 'duplicate_0123456789')
        self.assertEqual(first, self.repo.commit(draft['draftId'], 'duplicate_0123456789'))
        self.assertEqual(first, self.repo.commit(draft['draftId'], 'anotherkey_0123456789'))
        self.assertEqual(len(self.adapter.commits), 1)
        other = self.edited(answerMarkdown='另一个新的答案，不应复用之前的提交标识。')
        with self.assertRaises(RepoError):
            self.repo.commit(other['draftId'], 'duplicate_0123456789')

    def test_failed_write_and_failed_refresh_keep_good_content(self):
        draft = self.edited()
        original = self.repo.catalog()
        self.adapter.fail = True
        with self.assertRaises(RepoError):
            self.repo.commit(draft['draftId'], 'failure_0123456789')
        retained = self.repo.catalog(force=True)
        self.assertEqual(retained['revision'], original['revision'])
        self.assertTrue(retained['warning'])
        self.assertFalse(self.adapter.commits)
        self.adapter.fail = False
        self.assertEqual(self.repo.commit(draft['draftId'], 'failure_0123456789')['commit'], self.adapter.head())

    def test_unsafe_markdown_and_path_injection_rejected(self):
        with self.assertRaises(RepoError):
            self.edited(answerMarkdown='错误的标题会切断答案\n\n### A99 注入题\n\n意外新增题目。')
        with self.assertRaises(RepoError):
            self.edited(answerMarkdown='没有闭合的围栏会吞掉下一题\n```java\nint x = 1;')
        for path in ('../.env', 'docs/../README.md', '/etc/passwd', 'docs/new.md', 'web/src/app.mjs'):
            with self.assertRaises(RepoError):
                self.repo.preview({'operation':'create', 'documentPath':path, 'baseRevision':self.adapter.head(), 'title':'题目', 'answerMarkdown':'这个回答足够长，但路径不得越权。'})
        self.assertFalse(self.adapter.commits)

    def test_expiration_and_noop(self):
        now = [100.0]
        self.repo = ContentRepository(self.adapter, clock=lambda: now[0], draft_ttl=2)
        draft = self.edited()
        now[0] += 3
        with self.assertRaises(RepoError) as error:
            self.repo.commit(draft['draftId'], 'expired_0123456789')
        self.assertEqual(error.exception.code, 'draft_expired')
        with self.assertRaises(RepoError) as error:
            self.repo.preview(dict(self.repo.editable('docs/sample.md#a01'), operation='update'))
        self.assertEqual(error.exception.code, 'no_changes')

    def test_generated_answer_title_edit_keeps_id_and_canonical_generation(self):
        adapter = MemoryAdapter(self.actual)
        repo = ContentRepository(adapter)
        qid = next(k for k in parse_questions(self.actual) if k.startswith('questions/') and k.endswith('#q001'))
        original = repo.editable(qid)
        self.assertIn('公开面经证据', original['contextMarkdown'])
        updated_answer = original['answerMarkdown'] + ' 这里补充一个明确的适用边界。'
        draft = repo.preview(dict(original, operation='update', title=original['title']+'（补充）', answerMarkdown=updated_answer))
        self.assertIn('data/questions.json', draft['changedPaths'])
        result = repo.commit(draft['draftId'], 'generated_0123456789')
        self.assertEqual(result['questionId'], qid)
        self.assertIn(qid, parse_questions(adapter._files))
        row = next(q for q in json.loads(adapter._files['data/questions.json']) if q['id'] == 'Q001')
        self.assertEqual(row['answer'], updated_answer)
        self.assertEqual(row['source_path'], original['path'])
        generator = repo._generator()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'data').mkdir()
            for p in ('data/questions.json','data/sources.json','data/references.json'):
                (root/p).write_text(adapter._files[p])
            generated, _ = generator.collect_files(root)
        for p, content in generated.items():
            self.assertEqual(adapter._files[p], content, p)
        before, after = parse_questions(self.actual), parse_questions(adapter._files)
        self.assertEqual(set(before), set(after))
        for key in before:
            if key != qid:
                self.assertEqual(before[key]['answerMarkdown'], after[key]['answerMarkdown'])

    def test_fresh_remote_generator_template_is_not_rolled_back(self):
        adapter = MemoryAdapter(self.actual)
        repo = ContentRepository(adapter)
        repo.catalog()
        title = self.actual['README.md'].splitlines()[0]
        self.assertIn(title, self.actual['scripts/build.py'])
        new_title = title + '（其他维护者的新模板）'
        newer = {
            'README.md': self.actual['README.md'].replace(title, new_title, 1),
            'scripts/build.py': self.actual['scripts/build.py'].replace(title, new_title, 1),
        }
        adapter.atomic_commit(adapter.head(), newer, 'external template update', 'external')
        qid = next(k for k in parse_questions(self.actual) if k.startswith('questions/') and k.endswith('#q001'))
        fresh = repo.editable(qid)
        self.assertEqual(fresh['baseRevision'], adapter.head())
        with self.assertRaises(RepoError) as error:
            repo.preview(dict(fresh, operation='update', answerMarkdown=fresh['answerMarkdown']+' 补充正确的适用边界。'))
        self.assertEqual(error.exception.code, 'generator_version_conflict')
        self.assertEqual(error.exception.status, 409)
        self.assertFalse(repo._drafts)
        self.assertEqual(len(adapter.commits), 1)
        self.assertEqual(adapter._files['README.md'], newer['README.md'])
        self.assertEqual(adapter._files['scripts/build.py'], newer['scripts/build.py'])

    def test_manual_generated_content_difference_is_not_overwritten(self):
        adapter = MemoryAdapter(self.actual)
        repo = ContentRepository(adapter)
        repo.catalog()
        manual = self.actual['README.md'] + '\n维护者新增了必须保留的说明。\n'
        adapter.atomic_commit(adapter.head(), {'README.md': manual}, 'external README correction', 'external')
        qid = next(k for k in parse_questions(self.actual) if k.startswith('questions/') and k.endswith('#q001'))
        fresh = repo.editable(qid)
        with self.assertRaises(RepoError) as error:
            repo.preview(dict(fresh, operation='update', answerMarkdown=fresh['answerMarkdown']+' 补充正确的适用边界。'))
        self.assertEqual(error.exception.code, 'generator_version_conflict')
        self.assertFalse(repo._drafts)
        self.assertEqual(len(adapter.commits), 1)
        self.assertEqual(adapter._files['README.md'], manual)

    def test_missing_remote_generator_fails_closed(self):
        files = dict(self.actual)
        files.pop('scripts/build.py')
        adapter = MemoryAdapter(files)
        repo = ContentRepository(adapter)
        qid = next(k for k in parse_questions(files) if k.startswith('questions/') and k.endswith('#q001'))
        fresh = repo.editable(qid)
        with self.assertRaises(RepoError) as error:
            repo.preview(dict(fresh, operation='update', answerMarkdown=fresh['answerMarkdown']+' 补充正确的适用边界。'))
        self.assertEqual(error.exception.code, 'generator_version_conflict')
        self.assertFalse(adapter.commits)

    def test_generated_supplement_delete_regenerates_indexes(self):
        adapter, repo = MemoryAdapter(self.actual), None
        repo = ContentRepository(adapter)
        qid = next(k for k in parse_questions(self.actual) if k.startswith('supplements/'))
        original = repo.editable(qid)
        draft = repo.preview(dict(original, operation='delete'))
        self.assertIn('data/stats.json', draft['changedPaths'])
        self.assertIn(original['path'], draft['changedPaths'])
        repo.commit(draft['draftId'], 'delete_generated_0123456789')
        self.assertNotIn(original['path'], adapter._files)
        self.assertEqual(len(parse_questions(adapter._files)), 490)
        self.assertFalse(any(q['id']==original['number'] for q in json.loads(adapter._files['data/questions.json'])))

    def test_source_registry_export_is_explicit_and_fixed_commit(self):
        self.adapter._files['web/src/example.mjs'] = 'export const answer = 42;\n// Source example\n'
        self.adapter._save()
        registry = self.repo.source_repos()['repositories'][0]
        self.assertFalse(registry['allowModelExport'])
        with self.assertRaises(RepoError):
            self.repo.authorize_source('owner/private-project', True)
        with self.assertRaises(RepoError):
            self.repo.search_source('answer', repository='owner/private-project')
        self.repo.authorize_source(REPOSITORY, True)
        fixed = self.adapter.head()
        self.adapter.atomic_commit(fixed, {'web/src/example.mjs':'changed'}, 'external', 'external')
        value = self.repo.read_source('web/src/example.mjs', 1, 2, revision=fixed)
        self.assertIn('answer = 42', value['content'])
        self.assertIn(fixed, value['url'])
        self.assertTrue(value['allowModelExport'])
        results = self.repo.search_source('answer', revision=fixed)
        self.assertEqual(results['results'][0]['revision'], fixed)
        for path in ('../.env', '/etc/passwd', 'web/.deployment/config.json', 'data/secrets.json', '.git/config', 'web/node_modules/x.js'):
            with self.assertRaises(RepoError):
                self.repo.read_source(path, revision=fixed)
        with self.assertRaises(RepoError):
            self.repo.read_source('web/src/example.mjs', 1, 500, revision=fixed)

    def test_pending_commit_recovers_after_head_changed_without_second_write(self):
        class Uncertain(MemoryAdapter):
            def atomic_commit(inner, expected, changes, message, transaction):
                if getattr(inner, 'candidate', None):
                    return inner.candidate
                inner.candidate = super(Uncertain, inner).atomic_commit(expected, changes, message, transaction)
                raise RepoError('commit_uncertain', '模拟响应丢失。', 409)
        self.adapter = Uncertain(SIMPLE)
        self.repo = ContentRepository(self.adapter)
        draft = self.edited()
        with self.assertRaises(RepoError) as error:
            self.repo.commit(draft['draftId'], 'uncertain_0123456789')
        self.assertEqual(error.exception.code, 'commit_uncertain')
        result = self.repo.commit(draft['draftId'], 'uncertain_0123456789')
        self.assertEqual(result['commit'], self.adapter.head())
        self.assertEqual(len(self.adapter.commits), 1)

    def test_empty_catalog_delete_is_rejected_before_draft(self):
        adapter = MemoryAdapter({'docs/only.md':'# Single\n\n### A01 唯一题目\n\n完整的回答应该始终保留在非空题库中。\n'})
        repo = ContentRepository(adapter)
        with self.assertRaises(RepoError) as error:
            repo.preview(dict(repo.editable('docs/only.md#a01'), operation='delete'))
        self.assertEqual(error.exception.code, 'empty_catalog')
        self.assertFalse(repo._drafts)
        self.assertFalse(adapter.commits)

    def test_private_ai_proposal_requires_separate_public_confirmation(self):
        draft = self.edited()
        marked = self.repo.mark_private_proposal(draft['draftId'], {'repository':'hejulian2004/ssh_mobile',
            'revision':'b'*40, 'private':True, 'providerConfigVersion':'provider1', 'pathPrefixes':['lib/'],
            'content':'private code must not be included in marker metadata'})
        self.assertTrue(marked['requiresPublicConfirmation'])
        self.assertNotIn('content', marked['publicationDisclosure'])
        for unconfirmed in (False, 'true', 1, None):
            with self.assertRaises(RepoError) as error:
                self.repo.commit(draft['draftId'], 'private_0123456789', confirm_public_publication=unconfirmed)
            self.assertEqual(error.exception.code, 'public_publication_confirmation')
        self.assertFalse(self.adapter.commits)
        result = self.repo.commit(draft['draftId'], 'private_0123456789', confirm_public_publication=True)
        self.assertEqual(result['commit'], self.adapter.head())
        self.assertEqual(len(self.adapter.commits), 1)

    def test_parallel_reads_remain_parallel_during_tree_and_blob_eviction(self):
        class ParallelAdapter(MemoryAdapter):
            def __init__(inner):
                super().__init__({})
                inner.guard = threading.Lock()
                inner.tree_calls = inner.read_calls = 0
                inner.tree_barrier = threading.Barrier(4)
                inner.read_barrier = threading.Barrier(4)
            def tree(inner, revision):
                with inner.guard:
                    inner.tree_calls += 1
                    first = inner.tree_calls <= 4
                if first:
                    inner.tree_barrier.wait(timeout=3)
                return super().tree(revision)
            def read(inner, revision, path, entry=None):
                with inner.guard:
                    inner.read_calls += 1
                    first = inner.read_calls <= 4
                if first:
                    inner.read_barrier.wait(timeout=3)
                return super().read(revision, path, entry)
        adapter = ParallelAdapter()
        cases = []
        for version in range(20):
            adapter._files = {'docs/item%d.md' % n: '# Item\n\n### A01 Question\n\nAnswer version %d item %d retains its boundary.\n' % (version, n) for n in range(36)}
            adapter._save()
            cases.extend((adapter.head(), path, content) for path, content in adapter._files.items())
        repo = ContentRepository(adapter)
        with ThreadPoolExecutor(max_workers=4) as pool:
            result = list(pool.map(lambda item: repo._read(item[0], item[1]), cases))
        self.assertEqual(result, [case[2] for case in cases])
        self.assertEqual(adapter.read_calls, 720)
        self.assertLessEqual(len(repo._tree_cache), 8)
        self.assertLessEqual(len(repo._text_cache), 700)

    def test_github_500_unknown_patch_never_reposts_candidate(self):
        class StubGitHub(GitHubAdapter):
            def __init__(inner):
                inner._commit_candidates = {}
                inner.verify_fails = True
                inner.patches = inner.commit_posts = 0
            def head(inner):
                if inner.patches:
                    if inner.verify_fails:
                        raise RepoError('github_unavailable','模拟核实失败。',503)
                    return 'c'*40
                return 'a'*40
            def _request(inner, method, suffix, payload=None):
                if suffix == '/git/commits/'+'a'*40:
                    return {'tree': {'sha':'b'*40}}
                if suffix == '/git/blobs': return {'sha':'d'*40}
                if suffix == '/git/trees': return {'sha':'e'*40}
                if suffix == '/git/commits':
                    inner.commit_posts += 1
                    return {'sha':'c'*40}
                if method == 'PATCH':
                    inner.patches += 1
                    raise RepoError('github_failure','模拟GitHub500。',502)
                raise AssertionError((method,suffix))
        adapter = StubGitHub()
        with self.assertRaises(RepoError) as error:
            adapter.atomic_commit('a'*40, {'docs/sample.md':'new content'}, 'message', 'transaction')
        self.assertEqual(error.exception.code, 'commit_uncertain')
        self.assertEqual(adapter._commit_candidates['transaction'], 'c'*40)
        adapter.verify_fails = False
        self.assertEqual(adapter.atomic_commit('a'*40, {'docs/sample.md':'new content'}, 'message', 'transaction'), 'c'*40)
        self.assertEqual(adapter.patches,1)
        self.assertEqual(adapter.commit_posts,1)

if __name__ == '__main__': unittest.main()
