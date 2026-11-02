from io import BytesIO
import json
import http.client
import socket
import threading
import time
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, make_server
from .app import create_app, ThreadedWSGIServer, QuietHandler
from .tests_auth import config, PASSWORD


class FakeRepo:
    def __init__(self):
        self.calls = []
    def catalog(self, force=False):
        self.calls.append(('catalog', force))
        return {'version': 1, 'revision': 'a' * 40, 'files': [], 'origin': 'server-cache'}
    def editable(self, question_id, fresh=False):
        self.calls.append(('editable', question_id, True) if fresh else ('editable', question_id))
        return {'questionId': question_id}
    def preview(self, payload):
        self.calls.append(('preview', payload))
        return {'draftId': 'draft-one', 'diff': '+test'}
    def commit(self, draft, key, actor='admin', confirm_public_publication=False):
        self.calls.append(('commit', draft, key, actor, confirm_public_publication))
        return {'commit': 'b' * 40}
    def source_repos(self):
        return [{'repository': 'hejulian2004/android-interview-notes'}]
    def authorize_source(self, repository, allow):
        self.calls.append(('authorize', repository, allow))
        return {'allowModelExport': allow}
    def search_source(self, query, **kwargs):
        self.calls.append(('search', query, kwargs))
        return {'results': []}
    def read_source(self, path, **kwargs):
        self.calls.append(('read', path, kwargs))
        return {'path': path}


class FakeAI:
    def __init__(self):
        self.chat_sessions = []
        self.forgotten_sessions = []
    def public_settings(self):
        return {'configured': True, 'baseUrl': 'https://allowed.example/v1', 'model': 'test', 'keyConfigured': True}
    def configure(self, payload):
        return self.public_settings()
    def chat(self, payload, *, session_id):
        self.chat_sessions.append(session_id)
        return {'reply': 'test', 'citations': []}
    def forget_session(self, session_id):
        self.forgotten_sessions.append(session_id)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.time = 1000000
        self.repo = FakeRepo()
        self.app = create_app(config(), self.repo, FakeAI(), clock=lambda: self.time)
        self.cookies = ''
        self.csrf = ''

    def call(self, method, route, payload=None, *, origin='https://study.example', csrf=True, cookie=True):
        headers = {'Content-Type': 'application/json', 'Origin': origin}
        if cookie:
            headers['Cookie'] = self.cookies
        if csrf:
            headers['X-CSRF-Token'] = self.csrf
        body = json.dumps(payload or {}).encode()
        return self.app.dispatch(method, '/android-study/api/' + route, headers, body)

    def update_session(self, response):
        self.cookies = '; '.join(value.split(';', 1)[0] for name, value in response.headers if name == 'Set-Cookie')
        self.csrf = response.json()['csrfToken']

    def login(self):
        response = self.call('POST', 'login', {'username': 'admin', 'password': PASSWORD})
        self.assertEqual(response.status, 200)
        self.update_session(response)
        return response

    def test_every_business_endpoint_requires_auth_and_no_repo_calls(self):
        requests = [('GET', 'catalog'), ('POST', 'catalog/refresh'), ('GET', 'edit?questionId=docs/a.md%23a01'), ('POST', 'changes/preview'), ('POST', 'changes/commit'), ('GET', 'settings/model'), ('PUT', 'settings/model'), ('GET', 'source/repos'), ('POST', 'source/search'), ('POST', 'source/read'), ('POST', 'source/authorize'), ('POST', 'agent/chat')]
        for method, route in requests:
            with self.subTest(route=route):
                self.assertEqual(self.call(method, route).status, 401)
        self.assertEqual(self.repo.calls, [])

    def test_explicit_latest_edit_requires_auth_and_uses_strict_fresh_path(self):
        route = 'edit?questionId=docs/a.md%23a01&fresh=1'
        self.assertEqual(self.call('GET', route).status, 401)
        self.assertEqual(self.repo.calls, [])
        self.login()
        self.assertEqual(self.call('GET', route).status, 200)
        self.assertEqual(self.repo.calls[-1], ('editable', 'docs/a.md#a01', True))

    def test_trusted_proxy_client_buckets_are_isolated_and_cannot_be_forged(self):
        self.app = create_app(config(trusted_proxy_ips=('127.0.0.1',)), self.repo, FakeAI())
        def login_attempt(peer, claimed_client, password='wrong'):
            headers = {'Origin': 'https://study.example', 'Content-Type': 'application/json', 'X-Study-Client-IP': claimed_client}
            body = json.dumps({'username': 'admin', 'password': password}).encode()
            return self.app.dispatch('POST', '/android-study/api/login', headers, body, remote_addr=peer)
        for _ in range(5):
            self.assertEqual(login_attempt('127.0.0.1', '198.51.100.1').status, 401)
        self.assertEqual(login_attempt('127.0.0.1', '198.51.100.1').status, 429)
        self.assertEqual(login_attempt('127.0.0.1', '198.51.100.2', PASSWORD).status, 200)
        # An unknown peer cannot reset its bucket by claiming another client address.
        for index in range(5):
            self.assertEqual(login_attempt('203.0.113.1', f'198.51.100.{index + 10}').status, 401)
        self.assertEqual(login_attempt('203.0.113.1', '198.51.100.99', PASSWORD).status, 429)
        for malformed in ('198.51.100.2, 198.51.100.3', ' 198.51.100.2', 'unknown', 'fe80::1%eth0'):
            self.assertEqual(login_attempt('127.0.0.1', malformed, PASSWORD).status, 400)

    def test_cookie_flags_no_tokens_in_body_and_cross_site_login_denied(self):
        self.assertEqual(self.call('POST', 'login', {'username': 'admin', 'password': PASSWORD}, origin='https://attacker.example').status, 403)
        response = self.login()
        for name, value in response.headers:
            if name == 'Set-Cookie':
                for flag in ('HttpOnly', 'Secure', 'SameSite=Strict', 'Path=/android-study/api'):
                    self.assertIn(flag, value)
        self.assertNotIn('study_access', response.body.decode())
        self.assertEqual(self.call('GET', 'session').json()['user'], 'admin')

    def test_all_post_put_routes_require_origin_and_csrf(self):
        self.login()
        routes = [('POST', 'catalog/refresh'), ('POST', 'changes/preview'), ('POST', 'changes/commit'), ('PUT', 'settings/model'), ('POST', 'source/authorize'), ('POST', 'source/search'), ('POST', 'source/read'), ('POST', 'agent/chat'), ('POST', 'logout'), ('POST', 'session/refresh')]
        for method, route in routes:
            self.assertEqual(self.call(method, route, csrf=False).status, 403, route)
            self.assertEqual(self.call(method, route, origin='https://attacker.example').status, 403, route)
        self.assertEqual(self.repo.calls, [])

    def test_refresh_after_reload_and_logout_revokes_access(self):
        self.login()
        old_cookies = self.cookies
        self.time += 61
        expired = self.call('GET', 'session', csrf=False)
        self.assertEqual(expired.status, 401)
        self.assertTrue(expired.json()['needsRefresh'])
        self.csrf = expired.json()['csrfToken']
        refreshed = self.call('POST', 'session/refresh')
        self.assertEqual(refreshed.status, 200)
        self.update_session(refreshed)
        self.assertNotEqual(old_cookies, self.cookies)
        self.assertEqual(self.call('GET', 'catalog').status, 200)
        self.assertEqual(self.call('POST', 'logout').status, 200)
        self.assertEqual(self.call('GET', 'catalog').status, 401)
        self.assertEqual(self.call('POST', 'session/refresh').status, 401)

    def test_routes_delegate_with_revision_idempotency_and_no_untrusted_actor(self):
        self.login()
        self.assertEqual(self.call('GET', 'edit?questionId=docs/a.md%23a01').json()['questionId'], 'docs/a.md#a01')
        self.assertEqual(self.call('POST', 'changes/preview', {'baseRevision': 'a' * 40}).status, 200)
        self.assertEqual(self.call('POST', 'changes/commit', {'draftId': 'draft-one', 'idempotencyKey': 'same-request-123', 'actor': 'attacker'}).status, 200)
        self.assertEqual(self.repo.calls[-1][-2], 'admin')
        self.assertIs(self.repo.calls[-1][-1], False)
        self.assertEqual(self.call('POST', 'changes/commit', {'draftId': 'draft-one'}).status, 400)
        self.assertEqual(self.call('POST', 'catalog/refresh').status, 200)
        self.assertEqual(self.repo.calls[-1], ('catalog', True))
        self.assertEqual(self.call('POST', 'source/search', {'query': 'Handler', 'revision': 'a' * 40}).status, 200)
        self.assertEqual(self.call('POST', 'source/read', {'path': 'README.md', 'startLine': 2, 'endLine': 5}).status, 200)
        self.assertEqual(self.call('POST', 'source/authorize', {'repository': 'test'}).status, 400)
        self.assertEqual(self.call('GET', 'settings/model').status, 200)
        self.assertEqual(self.call('POST', 'agent/chat', {'message': 'hello'}).status, 200)

    def test_publication_confirmation_is_explicit_boolean_and_actor_is_server_owned(self):
        self.login()
        base = {'draftId': 'private-derived-draft', 'idempotencyKey': 'private-publication-123', 'actor': 'attacker'}
        for invalid in ('true', 1, None, [], {}):
            response = self.call('POST', 'changes/commit', {**base, 'confirmPublicPublication': invalid})
            self.assertEqual(response.status, 400)
        self.assertEqual(self.repo.calls, [])
        response = self.call('POST', 'changes/commit', {**base, 'confirmPublicPublication': True})
        self.assertEqual(response.status, 200)
        self.assertEqual(self.repo.calls[-1], ('commit', base['draftId'], base['idempotencyKey'], 'admin', True))
        response = self.call('POST', 'changes/commit', {**base, 'confirmPublicPublication': False})
        self.assertEqual(response.status, 200)
        self.assertIs(self.repo.calls[-1][-1], False)

    def test_agent_history_uses_authenticated_sid_and_logout_forgets_it(self):
        self.login()
        expected_sid = next(iter(self.app.auth.sessions))
        self.assertEqual(self.call('POST', 'agent/chat', {'message': 'first question'}).status, 200)
        self.assertEqual(self.app.ai.chat_sessions, [expected_sid])
        # A caller cannot select another session's conversation, even while logged in.
        for key in ('session', 'sessionId', 'session_id', 'owner', 'ownerId', 'owner_id'):
            response = self.call('POST', 'agent/chat', {'message': 'followup', key: 'another-admin-session'})
            self.assertEqual(response.status, 400, key)
        self.assertEqual(self.app.ai.chat_sessions, [expected_sid])
        self.assertEqual(self.call('POST', 'logout').status, 200)
        self.assertEqual(self.app.ai.forgotten_sessions, [expected_sid])
        self.assertNotIn(expected_sid, self.app.auth.sessions)

    def test_invalid_payload_and_internal_errors_are_safe(self):
        self.login()
        headers = {'Cookie': self.cookies, 'Origin': 'https://study.example', 'X-CSRF-Token': self.csrf, 'Content-Type': 'application/json'}
        for body in (b'{"operation":"delete","operation":"update"}', b'[]', b'\xff'):
            response = self.app.dispatch('POST', '/android-study/api/changes/preview', headers, body)
            self.assertEqual(response.status, 400)
        self.assertEqual(self.app.dispatch('POST', '/android-study/api/changes/preview', headers, b'x' * 524289).status, 413)
        self.repo.catalog = lambda **_: (_ for _ in ()).throw(RuntimeError('secret-token-must-not-leak'))
        response = self.call('GET', 'catalog')
        self.assertEqual(response.status, 500)
        self.assertNotIn('secret-token', response.body.decode())
        self.assertEqual(response.header('Cache-Control'), 'no-store')

    def test_disabled_ai_does_not_block_crud(self):
        self.app.ai = None
        self.login()
        self.assertFalse(self.call('GET', 'settings/model').json()['configured'])
        self.assertEqual(self.call('POST', 'agent/chat', {'message': 'hello'}).status, 503)
        self.assertEqual(self.call('POST', 'changes/preview', {'baseRevision': 'a' * 40}).status, 200)

    def test_wsgi_request_size_and_static_traversal(self):
        captured = []
        response = self.app({'REQUEST_METHOD': 'POST', 'PATH_INFO': '/android-study/api/login', 'CONTENT_LENGTH': '999999999', 'wsgi.input': BytesIO()}, lambda status, headers: captured.append(status))
        self.assertTrue(captured[0].startswith('413'))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'index.html').write_text('<h1>Login</h1>')
            (root / 'engine').mkdir()
            (root / 'engine' / 'snapshot.json').write_text('{"secret":"old-content"}')
            (root / 'link.html').symlink_to('/etc/passwd')
            self.app.config.static_root = directory
            self.assertEqual(self.app.dispatch('GET', '/android-study/').status, 200)
            for path in ('/android-study/../auth.py', '/android-study/%2e%2e/auth.py', '/android-study/engine/snapshot.json', '/android-study/link.html', '/android-study/.env', '/other/'):
                self.assertEqual(self.app.dispatch('GET', path).status, 404, path)
            self.assertIn("connect-src 'self'", self.app.dispatch('GET', '/android-study/').header('Content-Security-Policy'))


class ConnectionBoundTests(unittest.TestCase):
    def make_server_without_socket(self):
        # Exercise the real initialization without binding any local/production socket.
        with patch.object(WSGIServer, '__init__', return_value=None):
            return ThreadedWSGIServer(('127.0.0.1', 0), object)

    def test_connections_are_bounded_before_worker_creation_and_released(self):
        server = self.make_server_without_socket()
        server.shutdown_request = Mock()
        peer = ('127.0.0.1', 12345)
        with patch.object(ThreadingMixIn, 'process_request') as spawn:
            sockets = [object() for _ in range(server.max_concurrent_connections + 2)]
            for request in sockets:
                server.process_request(request, peer)
            self.assertEqual(spawn.call_count, server.max_concurrent_connections)
            self.assertEqual(server.shutdown_request.call_count, 2)
            server.shutdown_request.assert_any_call(sockets[-1])
            server.shutdown_request.assert_any_call(sockets[-2])
            # Even a failing request handler must return its connection slot.
            with patch.object(ThreadingMixIn, 'process_request_thread', side_effect=RuntimeError('handler failed')):
                with self.assertRaises(RuntimeError):
                    server.process_request_thread(sockets[0], peer)
            server.process_request(object(), peer)
            self.assertEqual(spawn.call_count, server.max_concurrent_connections + 1)
            server.process_request(object(), peer)
            self.assertEqual(server.shutdown_request.call_count, 3)

    def test_thread_start_failure_does_not_leak_capacity(self):
        server = self.make_server_without_socket()
        with patch.object(ThreadingMixIn, 'process_request', side_effect=RuntimeError('cannot start thread')):
            for _ in range(server.max_concurrent_connections + 1):
                with self.assertRaises(RuntimeError):
                    server.process_request(object(), ('127.0.0.1', 12345))
        # Every failed spawn returned its token; all initial capacity remains available.
        for _ in range(server.max_concurrent_connections):
            self.assertTrue(server.connection_slots.acquire(blocking=False))
        self.assertFalse(server.connection_slots.acquire(blocking=False))


class RequestReadDeadlineTests(unittest.TestCase):
    def setUp(self):
        class SmallDeadlineServer(ThreadedWSGIServer):
            max_concurrent_connections = 2
            request_read_deadline_seconds = 0.15
        self.repo = FakeRepo()
        self.app = create_app(config(), self.repo, FakeAI())
        self.server = make_server('127.0.0.1', 0, self.app, server_class=SmallDeadlineServer, handler_class=QuietHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()
        self.sockets = []

    def tearDown(self):
        for connection in self.sockets:
            connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)

    def open_socket(self):
        connection = socket.create_connection(self.server.server_address, timeout=1)
        connection.settimeout(1)
        self.sockets.append(connection)
        return connection

    def trickle(self, connections, prefix):
        for connection in connections:
            connection.sendall(prefix)
        until = time.monotonic() + 0.42
        while time.monotonic() < until:
            for connection in connections:
                try:
                    connection.sendall(b' ')
                except OSError:
                    pass
            time.sleep(0.02)
        for connection in connections:
            try:
                self.assertEqual(connection.recv(1), b'')
            except ConnectionResetError:
                pass
        # The former slow requests no longer own either of the only two slots.
        client = http.client.HTTPConnection(*self.server.server_address, timeout=1)
        try:
            client.request('GET', '/android-study/api/session')
            response = client.getresponse()
            self.assertEqual(response.status, 401)
            response.read()
        finally:
            client.close()
        self.assertEqual(self.repo.calls, [])

    def test_absolute_deadline_closes_slow_body_and_releases_worker_slots(self):
        connections = [self.open_socket(), self.open_socket()]
        self.trickle(connections, b'POST /android-study/api/catalog/refresh HTTP/1.1\r\nHost: localhost\r\nOrigin: https://attacker.example\r\nContent-Type: application/json\r\nContent-Length: 200\r\n\r\n')

    def test_absolute_deadline_also_covers_trickled_headers(self):
        connections = [self.open_socket(), self.open_socket()]
        self.trickle(connections, b'POST /android-study/api/login HTTP/1.1\r\nHost: localhost\r\nX-Slow: ')

    def test_truncated_body_is_rejected_without_dispatch(self):
        connection = self.open_socket()
        connection.sendall(b'POST /android-study/api/login HTTP/1.1\r\nHost: localhost\r\nOrigin: https://study.example\r\nContent-Type: application/json\r\nContent-Length: 20\r\n\r\n{}')
        connection.shutdown(socket.SHUT_WR)
        response = http.client.HTTPResponse(connection)
        response.begin()
        self.assertEqual(response.status, 400)
        self.assertEqual(json.loads(response.read())['error']['code'], 'truncated_request')
        self.assertEqual(self.repo.calls, [])

    def test_complete_body_disarms_deadline_before_slow_business_processing(self):
        client = http.client.HTTPConnection(*self.server.server_address, timeout=2)
        try:
            login_body = json.dumps({'username': 'admin', 'password': PASSWORD})
            client.request('POST', '/android-study/api/login', login_body, {'Origin': 'https://study.example', 'Content-Type': 'application/json'})
            response = client.getresponse()
            self.assertEqual(response.status, 200)
            cookies = '; '.join(value.split(';', 1)[0] for name, value in response.getheaders() if name.lower() == 'set-cookie')
            csrf = json.loads(response.read())['csrfToken']
            def slow_catalog(force=False):
                time.sleep(0.38)  # More than twice the entire request read budget.
                return {'version': 1, 'revision': 'a' * 40, 'files': []}
            self.repo.catalog = slow_catalog
            started = time.monotonic()
            client.request('POST', '/android-study/api/catalog/refresh', '{}', {'Cookie': cookies, 'Origin': 'https://study.example', 'X-CSRF-Token': csrf, 'Content-Type': 'application/json'})
            response = client.getresponse()
            self.assertEqual(response.status, 200)
            response.read()
            self.assertGreater(time.monotonic() - started, 0.3)
        finally:
            client.close()


if __name__ == '__main__':
    unittest.main()
