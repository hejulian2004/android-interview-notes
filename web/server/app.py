"""Same-origin JSON application and loopback-only WSGI entry point.

Production is deliberately unconfigured. create_app injects adapters for tests; importing
this module does not read secrets, touch GitHub, or start a network listener.
"""
from __future__ import annotations
from dataclasses import dataclass
from http import HTTPStatus
from http.cookies import SimpleCookie, CookieError
from io import BytesIO
import json
import mimetypes
from pathlib import Path
import re
import socket
from socketserver import ThreadingMixIn
import threading
from urllib.parse import parse_qs, unquote, urlsplit
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server
from .auth import Auth, AuthError, _json_no_duplicates
from .config import Config, ConfigurationError, require_loopback, github_token_provider


@dataclass
class Response:
    status: int
    body: bytes
    headers: list[tuple[str, str]]

    def json(self):
        return json.loads(self.body)

    def header(self, name, default=None):
        return next((v for k, v in self.headers if k.lower() == name.lower()), default)


def _json_response(value, status=200, headers=None):
    body = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    return Response(status, body, [('Content-Type', 'application/json; charset=utf-8'), ('Cache-Control', 'no-store'),
                                   ('X-Content-Type-Options', 'nosniff')] + (headers or []))


class App:
    def __init__(self, config, repository, ai=None, *, clock=None):
        self.config = config.validate()
        self.repository = repository
        self.ai = ai
        self.auth = Auth(config, **({'clock': clock} if clock is not None else {}))
        self.capacity = threading.BoundedSemaphore(24)

    def _cookies(self, headers):
        try:
            raw = headers.get('cookie', '')
            if len(raw) > 16384:
                raise CookieError()
            cookie = SimpleCookie()
            cookie.load(raw)
            return {name: item.value for name, item in cookie.items()}
        except CookieError:
            return {}

    def _cookie_headers(self, access='', refresh='', *, clear=False):
        path = self.config.api_prefix
        flags = '; HttpOnly; SameSite=Strict' + ('; Secure' if self.config.secure_cookies else '')
        access_age = 0 if clear else self.config.access_seconds
        refresh_age = 0 if clear else self.config.refresh_seconds
        return [('Set-Cookie', f'study_access={access}; Path={path}; Max-Age={access_age}{flags}'),
                ('Set-Cookie', f'study_refresh={refresh}; Path={path}; Max-Age={refresh_age}{flags}')]

    def _parse_payload(self, body, headers):
        if not isinstance(body, bytes) or len(body) > self.config.max_body_bytes:
            raise AuthError('body_too_large', '请求内容过大', 413)
        if headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
            raise AuthError('json_required', '请使用 JSON 请求', 415)
        try:
            value = json.loads(body or b'{}', object_pairs_hook=_json_no_duplicates)
            if not isinstance(value, dict):
                raise ValueError()
            return value
        except (ValueError, TypeError, UnicodeDecodeError, RecursionError):
            raise AuthError('invalid_json', 'JSON 请求格式不正确', 400) from None

    def dispatch(self, method, path, headers=None, body=b'', remote_addr='127.0.0.1'):
        """Transport-independent request API, used by integration tests without sockets."""
        if not self.capacity.acquire(blocking=False):
            return _json_response({'error': {'code': 'busy', 'message': '服务繁忙，请稍后重试'}}, 429)
        try:
            return self._dispatch(method.upper(), path, {str(k).lower(): str(v) for k, v in (headers or {}).items()}, body, remote_addr)
        except Exception as exc:
            # Known service errors carry only deliberately safe public messages.
            if isinstance(exc, AuthError) or (type(exc).__name__ in ('RepoError', 'AiError') and hasattr(exc, 'code')):
                status = getattr(exc, 'status', 400)
                return _json_response({'error': {'code': exc.code, 'message': exc.message}}, status)
            return _json_response({'error': {'code': 'internal_error', 'message': '服务暂时不可用，草稿尚未丢弃'}}, 500)
        finally:
            self.capacity.release()

    def _dispatch(self, method, path, headers, body, remote_addr):
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc or parsed.fragment:
            raise AuthError('invalid_path', '请求路径不正确', 400)
        if not (parsed.path == self.config.api_prefix or parsed.path.startswith(self.config.api_prefix + '/')):
            return self._static(method, parsed.path)
        route = parsed.path[len(self.config.api_prefix):].strip('/')
        cookies = self._cookies(headers)
        if method not in ('GET', 'POST', 'PUT'):
            raise AuthError('method_not_allowed', '请求方法不支持', 405)
        if method != 'GET':
            self.auth.check_origin(headers.get('origin'))
        if route == 'login' and method == 'POST':
            payload = self._parse_payload(body, headers)
            session, access, refresh = self.auth.login(payload.get('username'), payload.get('password'), self.auth.client_address(remote_addr, headers.get('x-study-client-ip')))
            return _json_response(self.auth.public_session(session), headers=self._cookie_headers(access, refresh))
        if route == 'session' and method == 'GET':
            try:
                session = self.auth.authenticate(cookies.get('study_access', ''))
                return _json_response(self.auth.public_session(session))
            except AuthError:
                try:
                    session = self.auth.refresh_session(cookies.get('study_refresh', ''))
                    return _json_response({'error': {'code': 'access_expired', 'message': '会话需要续期'},
                                           'needsRefresh': True, 'csrfToken': session.csrf}, 401)
                except AuthError:
                    raise AuthError('unauthenticated', '请先登录', 401) from None
        if route in ('session/refresh', 'logout') and method == 'POST':
            self._parse_payload(body, headers)
            session = self.auth.refresh_session(cookies.get('study_refresh', ''))
            self.auth.check_csrf(session, headers.get('x-csrf-token'))
            if route == 'logout':
                self.auth.logout(session)
                if self.ai is not None:
                    self.ai.forget_session(session.sid)
                return _json_response({'authenticated': False}, headers=self._cookie_headers(clear=True))
            session, access, refresh = self.auth.refresh(cookies.get('study_refresh', ''))
            return _json_response(self.auth.public_session(session), headers=self._cookie_headers(access, refresh))
        session = self.auth.authenticate(cookies.get('study_access', ''))
        payload = {}
        if method != 'GET':
            self.auth.check_csrf(session, headers.get('x-csrf-token'))
            payload = self._parse_payload(body, headers)
        try:
            query = parse_qs(parsed.query, max_num_fields=20)
        except ValueError:
            raise AuthError('invalid_query', '查询参数过多', 400) from None
        def get_one(name):
            values = query.get(name, [])
            if len(values) != 1 or not values[0]:
                raise AuthError('missing_parameter', '缺少必要查询参数', 400)
            return values[0]
        if route == 'catalog' and method == 'GET':
            return _json_response(self.repository.catalog(force=False))
        if route == 'catalog/refresh' and method == 'POST':
            return _json_response(self.repository.catalog(force=True))
        if route == 'edit' and method == 'GET':
            if query.get('fresh') == ['1']:
                return _json_response(self.repository.editable(get_one('questionId'), fresh=True))
            return _json_response(self.repository.editable(get_one('questionId')))
        if route == 'changes/preview' and method == 'POST':
            return _json_response(self.repository.preview(payload))
        if route == 'changes/commit' and method == 'POST':
            draft, idem = payload.get('draftId'), payload.get('idempotencyKey')
            if not isinstance(draft, str) or not isinstance(idem, str) or not re.fullmatch(r'[A-Za-z0-9_-]{12,128}', idem):
                raise AuthError('invalid_commit_request', '提交请求缺少有效草稿或幂等标识', 400)
            if 'confirmPublicPublication' in payload and type(payload['confirmPublicPublication']) is not bool:
                raise AuthError('invalid_publication_consent', '请明确确认是否将私有资料相关答案发布到公开仓库', 400)
            return _json_response(self.repository.commit(draft, idem, actor=session.username,
                confirm_public_publication=payload.get('confirmPublicPublication') is True))
        if route == 'source/repos' and method == 'GET':
            result = self.repository.source_repos()
            return _json_response(result if isinstance(result, dict) else {'repositories': result})
        if route == 'source/authorize' and method == 'POST':
            if type(payload.get('allowModelExport')) is not bool:
                raise AuthError('invalid_consent', '请明确源码外发授权选择', 400)
            return _json_response(self.repository.authorize_source(
                payload.get('repository'), payload['allowModelExport'],
                revision=payload.get('revision'),
                provider_config_version=payload.get('providerConfigVersion'),
                path_prefixes=payload.get('pathPrefixes')))
        if route == 'source/search' and method == 'POST':
            return _json_response(self.repository.search_source(payload.get('query'), repository=payload.get('repository'), revision=payload.get('revision')))
        if route == 'source/read' and method == 'POST':
            return _json_response(self.repository.read_source(payload.get('path'), start_line=payload.get('startLine', 1), end_line=payload.get('endLine', 120), repository=payload.get('repository'), revision=payload.get('revision')))
        if route == 'settings/model' and method in ('GET', 'PUT'):
            if self.ai is None:
                if method == 'GET':
                    return _json_response({'configured': False, 'baseUrl': '', 'model': '', 'keyConfigured': False})
                raise AuthError('model_not_configured', '模型服务尚未启用，题库编辑仍可使用', 503)
            return _json_response(self.ai.public_settings() if method == 'GET' else self.ai.configure(payload))
        if route == 'agent/chat' and method == 'POST':
            if self.ai is None:
                raise AuthError('model_not_configured', '模型服务尚未配置，题库编辑仍可使用', 503)
            if any(key in payload for key in ('session', 'sessionId', 'session_id', 'owner', 'ownerId', 'owner_id')):
                raise AuthError('invalid_request', '对话会话由服务器登录状态确定', 400)
            return _json_response(self.ai.chat(payload, session_id=session.sid))
        raise AuthError('not_found', '接口不存在', 404)

    def _static(self, method, path):
        if method not in ('GET', 'HEAD') or not self.config.static_root:
            return _json_response({'error': {'code': 'not_found', 'message': '资源不存在'}}, 404)
        prefix = self.config.api_prefix.rsplit('/', 1)[0]
        decoded = unquote(path)
        if decoded == prefix:
            return Response(308, b'', [('Location', prefix + '/')])
        if not decoded.startswith(prefix + '/') or '\\' in decoded or '\x00' in decoded:
            raise AuthError('not_found', '资源不存在', 404)
        rel = decoded[len(prefix) + 1:] or 'index.html'
        if any(part.startswith('.') or part in ('..', '') for part in rel.split('/')):
            raise AuthError('not_found', '资源不存在', 404)
        root = Path(self.config.static_root).resolve()
        candidate = root / rel
        target = candidate.resolve()
        if root not in target.parents or candidate.is_symlink() or not target.is_file():
            raise AuthError('not_found', '资源不存在', 404)
        if rel.startswith(('server/', 'engine/snapshot')) or target.suffix not in ('.html', '.mjs', '.js', '.css', '.svg', '.json', '.png', '.ico'):
            raise AuthError('not_found', '资源不存在', 404)
        content_type = mimetypes.guess_type(str(target))[0] or 'application/octet-stream'
        if target.suffix == '.mjs':
            content_type = 'text/javascript'
        return Response(200, b'' if method == 'HEAD' else target.read_bytes(), [('Content-Type', content_type), ('Cache-Control', 'no-cache'),
                    ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer'),
                    ('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'")])

    def __call__(self, environ, start_response):
        try:
            if environ.get('HTTP_TRANSFER_ENCODING'):
                raise AuthError('invalid_request', '请求传输格式不支持', 400)
            raw_length = environ.get('CONTENT_LENGTH', '')
            length = int(raw_length or 0)
            if length < 0 or length > self.config.max_body_bytes:
                raise AuthError('body_too_large', '请求内容过大', 413)
            headers = {key[5:].replace('_', '-'): value for key, value in environ.items() if key.startswith('HTTP_')}
            headers['Content-Type'] = environ.get('CONTENT_TYPE', '')
            path = environ.get('PATH_INFO', '/') + ('?' + environ['QUERY_STRING'] if environ.get('QUERY_STRING') else '')
            body = environ['wsgi.input'].read(length)
            # End the absolute *read* deadline before authentication, GitHub, or AI
            # processing. Cancellation and expiry share a lock in QuietHandler, so
            # a timer that has already started cannot later close a completed read.
            finish_read = environ.get('android_study.finish_request_read')
            if callable(finish_read) and not finish_read():
                raise AuthError('request_timeout', '请求读取超时，请保留草稿后重试', 408)
            if len(body) != length:
                raise AuthError('truncated_request', '请求正文不完整，尚未处理修改', 400)
            response = self.dispatch(environ.get('REQUEST_METHOD', 'GET'), path, headers, body, environ.get('REMOTE_ADDR', ''))
        except (ValueError, AuthError) as exc:
            response = _json_response({'error': {'code': getattr(exc, 'code', 'invalid_request'), 'message': getattr(exc, 'message', '请求格式不正确')}}, getattr(exc, 'status', 400))
        except (OSError, TimeoutError):
            response = _json_response({'error': {'code': 'request_timeout', 'message': '请求读取超时，请保留草稿后重试'}}, 408)
        finally:
            finish_read = environ.get('android_study.finish_request_read')
            if callable(finish_read):
                finish_read()
        start_response(f'{response.status} {HTTPStatus(response.status).phrase}', response.headers + [('Content-Length', str(len(response.body)))])
        return [response.body]


def create_app(config, repository, ai=None, **kwargs):
    return App(config, repository, ai, **kwargs)


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    request_queue_size = 24
    max_concurrent_connections = 32
    request_read_deadline_seconds = 15.0

    def __init__(self, *args, **kwargs):
        # Bound accepted sockets before creating a thread or reading request bodies.
        # App.capacity separately limits dispatch; it cannot stop slow HTTP clients.
        self.connection_slots = threading.BoundedSemaphore(self.max_concurrent_connections)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self.connection_slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            # Thread creation failed, so no worker exists to release its slot.
            self.connection_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.connection_slots.release()

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(35)
        return request, address


class QuietHandler(WSGIRequestHandler):
    def handle(self):
        # A socket idle timeout alone can be defeated by sending one byte before
        # each timeout. This timer instead bounds the whole header+body read phase.
        self._read_lock = threading.Lock()
        self._read_finished = False
        self._read_expired = False
        self._read_timer = threading.Timer(self.server.request_read_deadline_seconds, self._expire_request_read)
        self._read_timer.daemon = True
        self._read_timer.start()
        try:
            super().handle()
        except (OSError, TimeoutError):
            # Deadline shutdown may interrupt a header read or response write.
            # Do not emit request details or an expected transport traceback.
            pass
        finally:
            self._finish_request_read()

    def _expire_request_read(self):
        with self._read_lock:
            if self._read_finished:
                return
            self._read_expired = True
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def _finish_request_read(self):
        with self._read_lock:
            if self._read_expired:
                return False
            self._read_finished = True
            self._read_timer.cancel()
            return True

    def get_environ(self):
        environ = super().get_environ()
        # Internal callback; no incoming header can create this WSGI environment key.
        environ['android_study.finish_request_read'] = self._finish_request_read
        return environ

    def log_message(self, format, *args):
        # Do not log URLs, query strings, authentication material, payloads, model text.
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Android Study loopback backend (explicit configuration required)')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8183)
    args = parser.parse_args()
    try:
        require_loopback(args.host)
        if not 1024 <= args.port <= 65535:
            raise ConfigurationError('Use an unprivileged loopback port')
        config = Config.from_env()
        from .runtime import build_services
        repo, model = build_services(config)
        app = create_app(config, repo, model)
    except ConfigurationError as exc:
        parser.error(str(exc))
    # The explicit process launch is the only point that binds a socket.
    with make_server(args.host, args.port, app, server_class=ThreadedWSGIServer, handler_class=QuietHandler) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()
