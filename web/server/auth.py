"""Single-admin authentication with short HS256 JWTs and revocable refresh sessions."""
from __future__ import annotations
from collections import OrderedDict, deque
from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
import ipaddress
import re
import secrets
import threading
import time


class AuthError(Exception):
    def __init__(self, code, message, status=400):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def _unb64(value: str) -> bytes:
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('invalid base64')
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


def hash_password(password: str, *, iterations: int = 600000) -> str:
    if not isinstance(password, str) or len(password) < 12 or len(password.encode()) > 1024:
        raise ValueError('Use an administrator password of 12 or more characters')
    if not 600000 <= iterations <= 2000000:
        raise ValueError('Password iteration count out of bounds')
    salt = secrets.token_bytes(18)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
    return f'pbkdf2_sha256${iterations}${_b64(salt)}${_b64(digest)}'


def valid_password_hash(encoded: str) -> bool:
    try:
        algorithm, rounds, salt, digest = encoded.split('$')
        return algorithm == 'pbkdf2_sha256' and 600000 <= int(rounds) <= 2000000 and len(_unb64(salt)) >= 16 and len(_unb64(digest)) == 32
    except (ValueError, TypeError, AttributeError):
        return False


def verify_password(password: str, encoded: str) -> bool:
    if not isinstance(password, str) or len(password.encode()) > 1024 or not valid_password_hash(encoded):
        return False
    _, rounds, salt, digest = encoded.split('$')
    candidate = hashlib.pbkdf2_hmac('sha256', password.encode(), _unb64(salt), int(rounds))
    return hmac.compare_digest(candidate, _unb64(digest))


def _json_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


@dataclass
class Session:
    sid: str
    username: str
    csrf: str
    refresh_digest: str
    expires: int
    generation: int = 0
    access_expires: int = 0


class Auth:
    issuer = 'android-study'
    audience = 'android-study-admin'

    def __init__(self, config, *, clock=time.time):
        self.config = config.validate()
        self.clock = clock
        self.sessions: dict[str, Session] = {}
        self.attempts = OrderedDict()
        self.lock = threading.RLock()

    def _now(self):
        return int(self.clock())

    def _purge(self):
        now = self._now()
        for sid in [s for s, value in self.sessions.items() if value.expires <= now]:
            self.sessions.pop(sid, None)
        for key, values in list(self.attempts.items()):
            while values and values[0] <= now - self.config.login_window_seconds:
                values.popleft()
            if not values:
                self.attempts.pop(key, None)

    def _access_token(self, session):
        now = self._now()
        session.access_expires = min(now + self.config.access_seconds, session.expires)
        claims = {'iss': self.issuer, 'aud': self.audience, 'sub': session.username, 'sid': session.sid,
                  'iat': now, 'exp': session.access_expires,
                  'typ': 'access', 'gen': session.generation}
        body = _b64(b'{"alg":"HS256","typ":"JWT"}') + '.' + _b64(json.dumps(claims, separators=(',', ':')).encode())
        signature = hmac.new(self.config.jwt_secret.encode(), body.encode(), hashlib.sha256).digest()
        return body + '.' + _b64(signature)

    def _decode(self, token):
        try:
            if not isinstance(token, str) or len(token) > 4096:
                raise ValueError()
            header, payload, signature = token.split('.')
            expected = hmac.new(self.config.jwt_secret.encode(), (header + '.' + payload).encode(), hashlib.sha256).digest()
            if not hmac.compare_digest(expected, _unb64(signature)):
                raise ValueError()
            head = json.loads(_unb64(header), object_pairs_hook=_json_no_duplicates)
            if head != {'alg': 'HS256', 'typ': 'JWT'}:
                raise ValueError()
            claims = json.loads(_unb64(payload), object_pairs_hook=_json_no_duplicates)
            if not isinstance(claims, dict):
                raise ValueError()
            if claims.get('iss') != self.issuer or claims.get('aud') != self.audience or claims.get('typ') != 'access':
                raise ValueError()
            if type(claims.get('exp')) is not int or type(claims.get('iat')) is not int or type(claims.get('gen')) is not int:
                raise ValueError()
            if claims['exp'] <= self._now() or claims['iat'] > self._now() + 30:
                raise ValueError()
            return claims
        except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError):
            raise AuthError('unauthenticated', '登录已失效，请重新登录', 401) from None

    @staticmethod
    def _digest(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def client_address(self, remote_addr, proxy_header=None):
        """Trust one dedicated header only from explicitly registered numeric peers.

        The reverse proxy MUST overwrite X-Study-Client-IP using its direct remote
        address. X-Forwarded-For chains are deliberately never interpreted.
        """
        try:
            peer = str(ipaddress.ip_address(remote_addr))
        except (ValueError, TypeError):
            return 'unknown-peer'
        if peer not in self.config.trusted_proxy_ips:
            return peer
        if proxy_header is None:
            return peer
        if not isinstance(proxy_header, str) or proxy_header != proxy_header.strip() or '%' in proxy_header or len(proxy_header) > 64:
            raise AuthError('invalid_proxy_header', '代理客户端地址格式不正确', 400)
        try:
            return str(ipaddress.ip_address(proxy_header))
        except ValueError:
            raise AuthError('invalid_proxy_header', '代理客户端地址格式不正确', 400) from None

    def login(self, username, password, remote_addr):
        with self.lock:
            self._purge()
            key = str(remote_addr)[:128]
            if key not in self.attempts:
                if len(self.attempts) >= self.config.login_bucket_limit:
                    self.attempts.popitem(last=False)
                self.attempts[key] = deque()
            self.attempts.move_to_end(key)
            if len(self.attempts[key]) >= self.config.login_attempts:
                raise AuthError('login_rate_limited', '登录尝试过多，请稍后重试', 429)
            self.attempts[key].append(self._now())
            valid_name = isinstance(username, str) and hmac.compare_digest(username.encode(), self.config.admin_username.encode())
            # Hash is verified even when username is wrong to avoid name timing disclosure.
            valid_password = verify_password(password, self.config.admin_password_hash)
            if not valid_name or not valid_password:
                raise AuthError('invalid_credentials', '用户名或密码不正确', 401)
            self.attempts.pop(key, None)
            # Bound session memory and remove older sessions without weakening validation.
            if len(self.sessions) >= 100:
                oldest = next(iter(self.sessions))
                self.sessions.pop(oldest, None)
            refresh = secrets.token_urlsafe(48)
            session = Session(secrets.token_urlsafe(24), self.config.admin_username, secrets.token_urlsafe(32), self._digest(refresh), self._now() + self.config.refresh_seconds)
            self.sessions[session.sid] = session
            return session, self._access_token(session), session.sid + '.' + refresh

    def authenticate(self, access_token):
        claims = self._decode(access_token)
        with self.lock:
            self._purge()
            session = self.sessions.get(claims.get('sid'))
            if not session or session.username != claims.get('sub') or session.generation != claims['gen']:
                raise AuthError('unauthenticated', '登录已失效，请重新登录', 401)
            return session

    def refresh_session(self, refresh_token):
        with self.lock:
            self._purge()
            try:
                sid, token = refresh_token.split('.', 1)
                session = self.sessions.get(sid)
                if not session or not hmac.compare_digest(session.refresh_digest, self._digest(token)):
                    raise ValueError()
                return session
            except (AttributeError, ValueError):
                raise AuthError('unauthenticated', '登录已失效，请重新登录', 401) from None

    def refresh(self, refresh_token):
        with self.lock:
            session = self.refresh_session(refresh_token)
            new_refresh = secrets.token_urlsafe(48)
            session.refresh_digest = self._digest(new_refresh)
            session.generation += 1  # Previously issued access token is revoked as well.
            return session, self._access_token(session), session.sid + '.' + new_refresh

    def logout(self, session):
        with self.lock:
            self.sessions.pop(session.sid, None)

    def check_origin(self, origin):
        if origin != self.config.public_origin:
            raise AuthError('origin_rejected', '请求来源不受信任', 403)

    def check_csrf(self, session, token):
        if not isinstance(token, str) or not hmac.compare_digest(token.encode(), session.csrf.encode()):
            raise AuthError('csrf_rejected', '请求校验失效，请刷新后重试', 403)

    def public_session(self, session):
        return {'authenticated': True, 'user': session.username, 'csrfToken': session.csrf,
                'expiresAt': session.access_expires}
