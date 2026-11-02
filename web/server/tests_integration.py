"""Independent full-corpus HTTP-dispatch tests; adapters never access the network."""
from __future__ import annotations
from http.cookies import SimpleCookie
import json
from pathlib import Path
import unittest
from urllib.parse import urlencode

from .app import create_app
from .repository import ContentRepository, MemoryAdapter, parse_questions, REPOSITORY
from .ai import ModelService
from .sources import SourceRegistry, RepositoryWithSources
from .tests_auth import config, PASSWORD

ROOT = Path(__file__).resolve().parents[2]
QUESTION = 'docs/java-core-interview-guide.md#ja01'
PRIVATE_PROJECT = 'hejulian2004/ssh_mobile'
OTHER_PROJECT = 'hejulian2004/testDemo'


def corpus_files():
    files = {}
    for directory in ('docs', 'questions', 'supplements', 'sources', 'indexes', 'references', 'data'):
        for path in (ROOT / directory).rglob('*'):
            if path.is_file() and path.suffix in ('.md', '.json'):
                files[path.relative_to(ROOT).as_posix()] = path.read_text(encoding='utf-8')
    for name in ('README.md', 'METHODOLOGY.md', 'scripts/build.py'):
        files[name] = (ROOT / name).read_text(encoding='utf-8')
    return files


class ScriptedProvider:
    def __init__(self, outputs):
        self.outputs, self.calls = list(outputs), []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return {'choices': [{'message': self.outputs.pop(0)}]}


class ReadOnlySourceFixture:
    """A source transport deliberately has no write method, even in tests."""
    def __init__(self, repository, files, private=False):
        self.repository, self.private = repository, private
        self.memory = MemoryAdapter(files)
        self.calls = []

    def metadata(self):
        self.calls.append(('metadata',))
        return {'repository': self.repository, 'private': self.private,
                'visibilityVerified': True, 'defaultBranch': 'develop'}

    def head(self, branch):
        if branch != 'develop':
            raise AssertionError('source registry must use its actual default branch')
        return self.memory.head()

    def tree(self, revision):
        return self.memory.tree(revision)

    def read(self, revision, path, entry=None):
        self.calls.append(('read', revision, path))
        return self.memory.read(revision, path, entry)


def tool(name, args, identity='call_1'):
    return {'role': 'assistant', 'tool_calls': [{'id': identity, 'type': 'function',
             'function': {'name': name, 'arguments': json.dumps(args)}}]}


class CorpusIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = corpus_files()

    def setUp(self):
        self.time = 2_000_000
        self.adapter = MemoryAdapter(self.files)
        self.repository = ContentRepository(self.adapter, clock=lambda: self.time)
        self.app = create_app(config(), self.repository, clock=lambda: self.time)
        self.cookie, self.csrf = '', ''

    def call(self, method, route, payload=None, *, csrf=True):
        headers = {'Origin': 'https://study.example', 'Content-Type': 'application/json', 'Cookie': self.cookie}
        if csrf:
            headers['X-CSRF-Token'] = self.csrf
        response = self.app.dispatch(method, '/android-study/api/' + route,
                                     headers, json.dumps(payload or {}).encode())
        for name, value in response.headers:
            if name.lower() == 'set-cookie':
                cookie = SimpleCookie(); cookie.load(value)
                current = SimpleCookie(); current.load(self.cookie)
                for key, morsel in cookie.items():
                    current[key] = morsel.value
                self.cookie = '; '.join(key + '=' + morsel.value for key, morsel in current.items())
        return response

    def login(self):
        response = self.call('POST', 'login', {'username': 'admin', 'password': PASSWORD})
        self.assertEqual(response.status, 200)
        self.csrf = response.json()['csrfToken']

    def editable(self, question=QUESTION):
        response = self.call('GET', 'edit?' + urlencode({'questionId': question}))
        self.assertEqual(response.status, 200, response.json())
        return response.json()

    def update(self, question=QUESTION, **fields):
        edit = self.editable(question)
        change = dict(operation='update', questionId=question, baseRevision=edit['baseRevision'],
                      blobSha=edit['blobSha'], title=edit['title'], answerMarkdown=edit['answerMarkdown'] + '\n\n这是本地模拟集成测试中的新增说明。')
        change.update(fields)
        response = self.call('POST', 'changes/preview', change)
        self.assertEqual(response.status, 200, response.json())
        return response.json()

    def save(self, draft, identity='integration_idem_0001'):
        return self.call('POST', 'changes/commit', {'draftId': draft['draftId'], 'idempotencyKey': identity})

    def install_source_registry(self, outputs):
        self.source_adapters = {
            REPOSITORY: ReadOnlySourceFixture(REPOSITORY, self.files),
            PRIVATE_PROJECT: ReadOnlySourceFixture(PRIVATE_PROJECT, {
                'lib/feature.dart': 'class FixtureFeature {\n  final label = "PRIVATE_FIXTURE_ONLY";\n}\n',
                'src/outside.kt': 'class OutsideGrantedDirectory\n',
                'README.md': '# Private fixture project\n',
            }, private=True),
            OTHER_PROJECT: ReadOnlySourceFixture(OTHER_PROJECT, {'src/Main.kt': 'class PublicOtherProject\n'}),
        }
        self.registry = SourceRegistry(self.repository, lambda: 'never-used-fixture-credential',
            repositories=tuple(self.source_adapters), adapters=self.source_adapters,
            clock=lambda: self.time,
            provider_version=lambda: self.app.ai.public_settings()['configVersion'])
        self.wrapper = RepositoryWithSources(self.repository, self.registry)
        provider = ScriptedProvider(outputs)
        self.app.ai = ModelService({'model_allowed_hosts': ['model.example'],
            'model_base_url': 'https://model.example/v1', 'model_name': 'stub-model',
            'model_api_key': 'test-provider-key'}, self.wrapper, provider=provider)
        self.app.repository = self.wrapper
        return provider

    def test_real_491_baseline_auth_and_save_keeps_490_neighbors(self):
        self.assertEqual(self.call('GET', 'catalog').status, 401)
        self.assertEqual(self.adapter.commits, [])
        self.login()
        baseline = self.call('GET', 'catalog').json()
        before = parse_questions({f['path']: f for f in baseline['files']})
        self.assertEqual(len(before), 491)
        draft = self.update()
        self.assertIn('java-core-interview-guide.md', draft['diff'])
        self.assertEqual(self.adapter.commits, [], 'preview must not publish')
        saved = self.save(draft)
        self.assertEqual(saved.status, 200, saved.json())
        same = self.save(draft)
        self.assertEqual(same.status, 200, same.json())
        self.assertEqual(saved.json()['commit'], same.json()['commit'])
        self.assertEqual(len(self.adapter.commits), 1)
        latest = self.call('POST', 'catalog/refresh', {}).json()
        self.assertEqual(latest['revision'], saved.json()['commit'])
        after = parse_questions({f['path']: f for f in latest['files']})
        self.assertEqual(set(before), set(after))
        for identity in before:
            if identity != QUESTION:
                self.assertEqual(before[identity]['answerMarkdown'], after[identity]['answerMarkdown'], identity)
        self.assertIn('新增说明', self.editable()['answerMarkdown'])

    def test_cross_session_csrf_rejected_and_logout_revokes_business_access(self):
        self.login(); edit = self.editable()
        response = self.call('POST', 'changes/preview', dict(operation='delete', **edit), csrf=False)
        self.assertEqual(response.status, 403)
        self.assertEqual(self.adapter.commits, [])
        self.assertEqual(self.call('POST', 'logout').status, 200)
        self.assertEqual(self.call('GET', 'catalog').status, 401)
        self.assertEqual(self.call('POST', 'catalog/refresh', {}).status, 401)

    def test_stale_draft_and_github_failure_do_not_publish_or_lose_server_draft(self):
        self.login(); draft = self.update()
        self.adapter.fail = True
        failed = self.save(draft)
        self.assertEqual(failed.status, 503)
        self.assertEqual(self.adapter.commits, [])
        self.adapter.fail = False
        saved = self.save(draft)
        self.assertEqual(saved.status, 200, saved.json())
        stale = self.call('POST', 'changes/preview', {'operation': 'update', 'questionId': QUESTION,
            'baseRevision': draft['baseRevision'], 'blobSha': 'a' * 40, 'title': '冲突题目', 'answerMarkdown': '此处不是可直接覆盖远端的新答案。'})
        self.assertEqual(stale.status, 409)
        self.assertEqual(len(self.adapter.commits), 1)

    def test_generated_question_title_changes_preserve_id_and_canonical_data(self):
        self.login()
        question = next(identity for identity in parse_questions(self.files) if identity.startswith('questions/') and '#q001' in identity)
        edit = self.editable(question)
        draft = self.update(question, title='编辑后仍保留原始文件路径与学习进度')
        self.assertIn('data/questions.json', draft['changedPaths'])
        saved = self.save(draft)
        self.assertEqual(saved.status, 200, saved.json())
        self.assertEqual(saved.json()['questionId'], question)
        latest = self.call('GET', 'catalog').json()
        parsed = parse_questions({f['path']: f for f in latest['files']})
        self.assertEqual(len(parsed), 491)
        self.assertIn(question, parsed)
        row = next(r for r in json.loads(self.adapter.read(saved.json()['commit'], 'data/questions.json')) if r['id'] == 'Q001')
        self.assertEqual(row['source_path'], edit['path'])
        self.assertEqual(row['answer'], self.editable(question)['answerMarkdown'])

    def test_create_delete_create_never_reuses_deleted_question_id(self):
        self.login()
        path = 'docs/java-core-interview-guide.md'
        before = parse_questions(self.files)
        created = []
        for index in range(2):
            revision = self.call('GET', 'catalog').json()['revision']
            preview = self.call('POST', 'changes/preview', {'operation': 'create',
                'documentPath': path, 'baseRevision': revision,
                'title': '本地集成新增练习', 'answerMarkdown': '这是新增练习的模拟回答，不会写入真实 GitHub 仓库。'})
            self.assertEqual(preview.status, 200, preview.json())
            saved = self.save(preview.json(), 'integration_create_000' + str(index))
            self.assertEqual(saved.status, 200, saved.json())
            created.append(saved.json()['questionId'])
            if index == 0:
                edit = self.editable(created[-1])
                removed = self.call('POST', 'changes/preview', {'operation': 'delete',
                    'questionId': created[-1], 'baseRevision': edit['baseRevision'], 'blobSha': edit['blobSha']})
                self.assertEqual(removed.status, 200, removed.json())
                self.assertEqual(self.save(removed.json(), 'integration_delete_0001').status, 200)
        self.assertNotEqual(created[0], created[1])
        latest = self.call('GET', 'catalog').json()
        after = parse_questions({f['path']: f for f in latest['files']})
        self.assertEqual(len(after), 492)
        self.assertNotIn(created[0], after)
        for identity in before:
            self.assertEqual(before[identity]['answerMarkdown'], after[identity]['answerMarkdown'], identity)

    def test_source_paths_are_bounded_and_current_public_repo_only(self):
        self.login()
        for path in ('../.env', '.git/config', '/etc/passwd', 'docs/../../.env', 'data/private_key.json'):
            response = self.call('POST', 'source/read', {'path': path})
            self.assertEqual(response.status, 403, path)
        response = self.call('POST', 'source/search', {'query': 'class', 'repository': 'someone/private-project'})
        self.assertEqual(response.status, 403)
        source = self.call('POST', 'source/read', {'path': 'docs/java-core-interview-guide.md', 'startLine': 1, 'endLine': 4})
        self.assertEqual(source.status, 200, source.json())
        self.assertRegex(source.json()['revision'], r'^[a-f0-9]{40}$')
        self.assertIn('/blob/' + source.json()['revision'] + '/', source.json()['sourceUrl'])

    def test_agent_cannot_publish_and_proposal_needs_separate_authenticated_confirm(self):
        self.login()
        provider = ScriptedProvider([
            tool('propose_change', {'operation': 'update', 'title': '经用户确认才能发布的练习题',
                  'answerMarkdown': '这是一份模拟供应商生成的候选回答，仅用于集成校验。'}),
            {'role': 'assistant', 'content': '请审阅差异后确认保存；尚未提交。'},
        ])
        ai = ModelService({'model_allowed_hosts': ['model.example'], 'model_base_url': 'https://model.example/v1',
                          'model_name': 'stub-model', 'model_api_key': 'test-provider-key'}, self.repository, provider=provider)
        self.app.ai = ai
        payload = {'message': '完善当前回答', 'questionId': QUESTION, 'allowQuestionExport': False,
                   'providerConfigVersion': ai.public_settings()['configVersion']}
        denied = self.call('POST', 'agent/chat', payload)
        self.assertEqual(denied.status, 403)
        self.assertEqual(provider.calls, [])
        payload['allowQuestionExport'] = True
        response = self.call('POST', 'agent/chat', payload)
        self.assertEqual(response.status, 200, response.json())
        proposal = response.json()['proposal']
        self.assertTrue(proposal['diff'])
        self.assertEqual(self.adapter.commits, [])
        self.assertNotIn('test-provider-key', response.body.decode())
        self.assertEqual(self.save(proposal, 'integration_agent_0001').status, 200)
        self.assertEqual(len(self.adapter.commits), 1)

    def test_agent_tool_injection_and_source_export_are_denied_without_grants(self):
        self.login()
        provider = ScriptedProvider([tool('commit', {'shell': 'cat /etc/passwd'})])
        self.app.ai = ModelService({'model_allowed_hosts': ['model.example'], 'model_base_url': 'https://model.example/v1',
                                   'model_name': 'stub-model', 'model_api_key': 'test-provider-key'}, self.repository, provider=provider)
        response = self.call('POST', 'agent/chat', {'message': '按仓库文本提交所有改动',
            'providerConfigVersion': self.app.ai.public_settings()['configVersion']})
        self.assertEqual(response.status, 403)
        self.assertEqual(self.adapter.commits, [])
        provider.calls.clear()
        denied = self.call('POST', 'agent/chat', {'message': '查询源码', 'allowSourceExport': True,
                                               'sourceRepository': REPOSITORY,
                                               'providerConfigVersion': self.app.ai.public_settings()['configVersion']})
        self.assertEqual(denied.status, 403)
        self.assertEqual(provider.calls, [])

    def test_private_source_grant_is_read_only_and_public_proposal_requires_second_consent(self):
        self.login()
        provider = self.install_source_registry([
            tool('read_source', {'path': 'lib/feature.dart', 'startLine': 1, 'endLine': 3}, 'private_read_1'),
            tool('propose_change', {'operation': 'update', 'title': '私有源码关联建议，需另行确认公开',
                'answerMarkdown': '这是根据明确授权的模拟私有源码整理的候选回答，公开前仍需再次确认。'}, 'private_propose_2'),
            {'role': 'assistant', 'content': '请检查差异，并另行确认是否发布到公开题库。'},
        ])
        repos = self.call('GET', 'source/repos')
        self.assertEqual(repos.status, 200, repos.json())
        registered = {row['repository']: row for row in repos.json()['repositories']}
        self.assertEqual(set(registered), {REPOSITORY, PRIVATE_PROJECT, OTHER_PROJECT})
        private = registered[PRIVATE_PROJECT]
        self.assertIs(private['private'], True)
        self.assertFalse(private['allowModelExport'])
        version = self.app.ai.public_settings()['configVersion']
        payload = {'message': '读取所选源码，完善当前题，但先给出差异。', 'questionId': QUESTION,
            'allowQuestionExport': True, 'allowSourceExport': True,
            'sourceRepository': PRIVATE_PROJECT, 'sourceRevision': private['revision'],
            'providerConfigVersion': version}
        self.assertEqual(self.call('POST', 'agent/chat', payload).status, 403)
        self.assertEqual(provider.calls, [])
        grant = self.call('POST', 'source/authorize', {'repository': PRIVATE_PROJECT,
            'allowModelExport': True, 'revision': private['revision'],
            'providerConfigVersion': version, 'pathPrefixes': ['lib/feature.dart']})
        self.assertEqual(grant.status, 200, grant.json())
        granted = next(row for row in grant.json()['repositories'] if row['repository'] == PRIVATE_PROJECT)
        self.assertEqual(granted['authorization']['pathPrefixes'], ['lib/feature.dart'])
        self.assertEqual(granted['authorization']['providerConfigVersion'], version)
        result = self.call('POST', 'agent/chat', payload)
        self.assertEqual(result.status, 200, result.json())
        proposal = result.json()['proposal']
        self.assertIs(proposal['requiresPublicConfirmation'], True)
        self.assertEqual(proposal['sourceDisclosure']['repository'], PRIVATE_PROJECT)
        self.assertIn('PRIVATE_FIXTURE_ONLY', json.dumps(provider.calls[1]['messages']))
        self.assertEqual(self.adapter.commits, [])
        request = {'draftId': proposal['draftId'], 'idempotencyKey': 'private_publication_integration_01'}
        denied = self.call('POST', 'changes/commit', request)
        self.assertEqual(denied.status, 403, denied.json())
        self.assertEqual(denied.json()['error']['code'], 'public_publication_confirmation')
        self.assertEqual(self.adapter.commits, [])
        saved = self.call('POST', 'changes/commit', {**request, 'confirmPublicPublication': True})
        self.assertEqual(saved.status, 200, saved.json())
        self.assertEqual(len(self.adapter.commits), 1)
        self.assertEqual(saved.json()['questionId'], QUESTION)
        for source_adapter in self.source_adapters.values():
            self.assertFalse(hasattr(source_adapter, 'atomic_commit'))
            self.assertEqual(source_adapter.memory.commits, [])

    def test_registered_private_source_model_tool_cannot_expand_path_or_supplier_grant(self):
        self.login()
        provider = self.install_source_registry([tool('read_source', {'path': 'src/outside.kt'})])
        rows = self.call('GET', 'source/repos').json()['repositories']
        private = next(row for row in rows if row['repository'] == PRIVATE_PROJECT)
        version = self.app.ai.public_settings()['configVersion']
        grant = {'repository': PRIVATE_PROJECT, 'allowModelExport': True, 'revision': private['revision'],
                 'providerConfigVersion': version, 'pathPrefixes': ['lib/']}
        wrong = self.call('POST', 'source/authorize', {**grant, 'providerConfigVersion': 'stale-supplier'})
        self.assertEqual(wrong.status, 409, wrong.json())
        self.assertEqual(self.call('POST', 'source/authorize', grant).status, 200)
        query = {'message': '查询范围内的源码', 'allowSourceExport': True,
                 'sourceRepository': PRIVATE_PROJECT, 'sourceRevision': private['revision'],
                 'providerConfigVersion': version}
        result = self.call('POST', 'agent/chat', query)
        self.assertEqual(result.status, 403, result.json())
        self.assertEqual(len(provider.calls), 1)
        self.assertFalse(any(call[0] == 'read' and call[2] == 'src/outside.kt'
                             for call in self.source_adapters[PRIVATE_PROJECT].calls))
        self.assertEqual(self.adapter.commits, [])

    def test_conversation_followups_are_bound_to_real_login_session_and_logout_erases_them(self):
        provider = ScriptedProvider([
            {'role': 'assistant', 'content': '只属于会话甲的解释。'},
            {'role': 'assistant', 'content': '这是会话甲的继续解释。'},
            {'role': 'assistant', 'content': '这是独立会话乙的解释。'},
            {'role': 'assistant', 'content': '这是重新登录后的新解释。'},
        ])
        self.app.ai = ModelService({'model_allowed_hosts': ['model.example'],
            'model_base_url': 'https://model.example/v1', 'model_name': 'stub-model',
            'model_api_key': 'test-provider-key'}, self.repository, provider=provider)
        conversation = 'integration_history_conv_01'
        self.login()
        first_sid = next(iter(self.app.auth.sessions))
        first_cookie, first_csrf = self.cookie, self.csrf
        payload = {'conversationId': conversation, 'message': '会话甲独有的第一段上下文',
                   'providerConfigVersion': self.app.ai.public_settings()['configVersion']}
        self.assertEqual(self.call('POST', 'agent/chat', payload).status, 200)
        payload['message'] = '沿着上一段继续解释'
        self.assertEqual(self.call('POST', 'agent/chat', payload).status, 200)
        followup = json.dumps(provider.calls[1]['messages'], ensure_ascii=False)
        self.assertIn('会话甲独有的第一段上下文', followup)
        self.assertIn('只属于会话甲的解释', followup)
        # The browser chooses the conversation ID, but only the authenticated
        # server SID can select its history owner.
        self.login()
        payload['message'] = '相同对话编号的新登录会话乙'
        self.assertEqual(self.call('POST', 'agent/chat', payload).status, 200)
        isolated = json.dumps(provider.calls[2]['messages'], ensure_ascii=False)
        self.assertNotIn('会话甲独有', isolated)
        self.assertNotIn('只属于会话甲', isolated)
        self.cookie, self.csrf = first_cookie, first_csrf
        self.assertEqual(self.call('POST', 'logout').status, 200)
        self.assertTrue(all(owner != first_sid for owner, _ in self.app.ai._histories))
        self.assertEqual(self.call('POST', 'agent/chat', payload).status, 401)
        self.login()
        payload['message'] = '退出后重新登录，再用相同编号'
        self.assertEqual(self.call('POST', 'agent/chat', payload).status, 200)
        fresh = json.dumps(provider.calls[3]['messages'], ensure_ascii=False)
        self.assertNotIn('会话甲独有', fresh)
        self.assertNotIn('独立会话乙', fresh)
        self.assertEqual(self.adapter.commits, [])


if __name__ == '__main__':
    unittest.main()
