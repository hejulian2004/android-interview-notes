import base64
import hashlib
import hmac
import json
import unittest
from unittest.mock import patch
from .auth import Auth, AuthError, hash_password, verify_password, valid_password_hash
from .config import Config, ConfigurationError, require_loopback

PASSWORD = 'local-test-password-only'
PASSWORD_HASH = hash_password(PASSWORD)


def config(**overrides):
    values = dict(public_origin='https://study.example', jwt_secret='test-only-signing-secret-32-bytes-minimum', admin_username='admin', admin_password_hash=PASSWORD_HASH, access_seconds=60, refresh_seconds=3600)
    values.update(overrides)
    return Config(**values)


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.time = 1000000
        self.auth = Auth(config(), clock=lambda: self.time)

    def assert_error(self, code, fn, *args):
        with self.assertRaises(AuthError) as exc:
            fn(*args)
        self.assertEqual(exc.exception.code, code)

    def test_missing_configuration_fails_closed(self):
        for conf in (Config(), config(jwt_secret='short'), config(admin_password_hash='plaintext'), config(public_origin='http://public.example'), config(secure_cookies=False)):
            with self.assertRaises(ConfigurationError):
                conf.validate()

    def test_hash_password_and_verification(self):
        self.assertTrue(valid_password_hash(PASSWORD_HASH))
        self.assertTrue(verify_password(PASSWORD, PASSWORD_HASH))
        self.assertFalse(verify_password('incorrect', PASSWORD_HASH))
        self.assertFalse(verify_password('x' * 1025, PASSWORD_HASH))
        with self.assertRaises(ValueError):
            hash_password('short')
        self.assertNotIn(PASSWORD, repr(config()))

    def test_login_expiry_rotation_replay_and_logout(self):
        session, access, refresh = self.auth.login('admin', PASSWORD, 'peer')
        self.assertEqual(self.auth.authenticate(access).sid, session.sid)
        self.time += 60
        self.assert_error('unauthenticated', self.auth.authenticate, access)
        session, access2, refresh2 = self.auth.refresh(refresh)
        self.assertNotEqual(refresh, refresh2)
        self.assert_error('unauthenticated', self.auth.refresh, refresh)
        self.assertEqual(self.auth.authenticate(access2).sid, session.sid)
        self.auth.logout(session)
        self.assert_error('unauthenticated', self.auth.authenticate, access2)
        self.assert_error('unauthenticated', self.auth.refresh, refresh2)

    def test_refresh_revokes_prior_access_and_absolute_session_expires(self):
        session, access, refresh = self.auth.login('admin', PASSWORD, 'peer')
        _, access2, refresh2 = self.auth.refresh(refresh)
        self.assert_error('unauthenticated', self.auth.authenticate, access)
        self.time += 3600
        self.assert_error('unauthenticated', self.auth.refresh, refresh2)
        self.assert_error('unauthenticated', self.auth.authenticate, access2)

    def test_tampered_jwt_none_algorithm_wrong_claims_rejected(self):
        _, access, _ = self.auth.login('admin', PASSWORD, 'peer')
        header, payload, signature = access.split('.')
        self.assert_error('unauthenticated', self.auth.authenticate, header + '.' + payload + '.AAAA')
        def encoded(value):
            return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip('=')
        def signed(h, p):
            body = h + '.' + p
            sig = base64.urlsafe_b64encode(hmac.new(self.auth.config.jwt_secret.encode(), body.encode(), hashlib.sha256).digest()).decode().rstrip('=')
            return body + '.' + sig
        self.assert_error('unauthenticated', self.auth.authenticate, signed(encoded({'alg': 'none', 'typ': 'JWT'}), payload))
        claims = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
        claims['aud'] = 'other-service'
        self.assert_error('unauthenticated', self.auth.authenticate, signed(header, encoded(claims)))
        claims['aud'] = 'android-study-admin'
        claims['exp'] = True
        self.assert_error('unauthenticated', self.auth.authenticate, signed(header, encoded(claims)))

    def test_limits_origin_csrf_and_username_are_not_bypassed(self):
        for i in range(5):
            self.assert_error('invalid_credentials', self.auth.login, 'wrong', PASSWORD, 'peer')
        self.assert_error('login_rate_limited', self.auth.login, 'admin', PASSWORD, 'peer')
        self.time += 900
        session, _, _ = self.auth.login('admin', PASSWORD, 'peer')
        self.assert_error('origin_rejected', self.auth.check_origin, 'https://study.example.attacker.test')
        self.assert_error('origin_rejected', self.auth.check_origin, None)
        self.assert_error('csrf_rejected', self.auth.check_csrf, session, '错误')
        self.auth.check_csrf(session, session.csrf)
        self.auth.check_origin('https://study.example')
        unicode_auth = Auth(config(admin_username='管理员'))
        unicode_auth.login('管理员', PASSWORD, 'peer')

    def test_login_bucket_memory_is_bounded_and_proxy_configuration_is_explicit(self):
        auth = Auth(config(login_bucket_limit=3))
        with patch('web.server.auth.verify_password', return_value=False):
            for index in range(10):
                self.assert_error('invalid_credentials', auth.login, 'admin', 'wrong', f'198.51.100.{index}')
                self.assertLessEqual(len(auth.attempts), 3)
        self.assertEqual(len(auth.attempts), 3)
        with self.assertRaises(ConfigurationError):
            config(trusted_proxy_ips=('127.0.0.0/8',)).validate()
        self.assertEqual(auth.client_address('198.51.100.1', 'forged-value'), '198.51.100.1')

    def test_explicit_loopback_development_only(self):
        config(public_origin='http://127.0.0.1:8183', allow_insecure_local_dev=True, secure_cookies=False).validate()
        for host in ('0.0.0.0', '8.8.8.8', 'localhost'):
            with self.assertRaises(ConfigurationError):
                require_loopback(host)
        for host in ('127.0.0.1', '::1'):
            require_loopback(host)


if __name__ == '__main__':
    unittest.main()
