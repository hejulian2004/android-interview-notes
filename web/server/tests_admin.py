import contextlib
import getpass
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from .admin import initialize, main, InitializationError
from .auth import verify_password
from .config import Config, ConfigurationError, read_private_file
from .tests_auth import config, PASSWORD, PASSWORD_HASH


class AdminInitializationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name) / 'config'
        self.directory.mkdir(mode=0o700)
        self.jwt = self.directory / 'jwt-secret'
        self.jwt.write_text('test-only-prepared-signing-secret-32-bytes-minimum')
        self.jwt.chmod(0o600)

    def tearDown(self):
        self.temporary.cleanup()

    def prompt(self, values):
        iterator = iter(values)
        return lambda _: next(iterator)

    def test_interactive_init_writes_only_private_hash_and_preserves_jwt(self):
        original_stat = self.jwt.stat()
        original = self.jwt.read_bytes()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = initialize(self.directory, username='admin', password_prompt=self.prompt([PASSWORD, PASSWORD]))
        target = self.directory / 'admin-password-hash'
        self.assertTrue(result['ready'])
        self.assertTrue(verify_password(PASSWORD, target.read_text().strip()))
        self.assertNotIn(PASSWORD, target.read_text())
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.jwt.read_bytes(), original)
        self.assertEqual(self.jwt.stat().st_ino, original_stat.st_ino)
        self.assertEqual(output.getvalue(), '')
        self.assertFalse((self.directory / 'admin-init.lock').exists())
        self.assertEqual(sorted(p.name for p in self.directory.iterdir()), ['admin-password-hash', 'jwt-secret'])

    def test_no_default_password_mismatch_or_missing_jwt_write_nothing(self):
        for values in ([PASSWORD, PASSWORD + '-different'], ['short', 'short']):
            with self.assertRaises(InitializationError):
                initialize(self.directory, username='admin', password_prompt=self.prompt(values))
            self.assertFalse((self.directory / 'admin-password-hash').exists())
        self.jwt.unlink()
        with self.assertRaises(InitializationError):
            initialize(self.directory, username='admin', password_prompt=lambda _: self.fail('must not prompt without JWT metadata'))

    def test_existing_hash_requires_explicit_replace_and_symlinks_are_rejected(self):
        target = self.directory / 'admin-password-hash'
        target.write_text('old-hash')
        target.chmod(0o600)
        with self.assertRaises(InitializationError):
            initialize(self.directory, username='admin', password_prompt=lambda _: self.fail('must not prompt before overwrite approval'))
        self.assertEqual(target.read_text(), 'old-hash')
        initialize(self.directory, username='admin', replace=True, password_prompt=self.prompt([PASSWORD, PASSWORD]))
        self.assertTrue(verify_password(PASSWORD, target.read_text().strip()))
        target.unlink()
        target.symlink_to(self.jwt)
        with self.assertRaises(InitializationError):
            initialize(self.directory, username='admin', replace=True, password_prompt=self.prompt([PASSWORD, PASSWORD]))
        target.unlink()
        alias = self.directory.parent / 'alias'
        alias.symlink_to(self.directory, target_is_directory=True)
        with self.assertRaises(InitializationError):
            initialize(alias, username='admin', password_prompt=self.prompt([PASSWORD, PASSWORD]))

    def test_unsafe_directory_and_noecho_fallback_are_rejected(self):
        self.directory.chmod(0o755)
        with self.assertRaises(InitializationError):
            initialize(self.directory, username='admin', password_prompt=self.prompt([PASSWORD, PASSWORD]))
        self.directory.chmod(0o700)
        def fallback(_):
            import warnings
            warnings.warn('no terminal', getpass.GetPassWarning)
        with self.assertRaises(InitializationError):
            initialize(self.directory, username='admin', password_prompt=fallback)
        self.assertFalse((self.directory / 'admin-password-hash').exists())
        with patch('sys.stdin.isatty', return_value=False), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(['initialize', '--directory', str(self.directory), '--username', 'admin'])

    def test_file_config_precedence_no_inline_fallback_and_repository_metadata(self):
        target = self.directory / 'admin-password-hash'
        target.write_text(PASSWORD_HASH)
        target.chmod(0o600)
        env = {'STUDY_PUBLIC_ORIGIN': 'https://study.example', 'STUDY_ADMIN_USERNAME': 'admin',
               'STUDY_JWT_SECRET_FILE': str(self.jwt), 'STUDY_ADMIN_PASSWORD_HASH_FILE': str(target),
               'STUDY_JWT_SECRET': 'ignored-inline', 'STUDY_ADMIN_PASSWORD_HASH': 'ignored-inline',
               'STUDY_TRUSTED_PROXY_IPS': '127.0.0.1,::1',
               'STUDY_SOURCE_REPOSITORIES': 'hejulian2004/android-interview-notes,owner/explicit-source'}
        with patch.dict(os.environ, env, clear=True):
            configured = Config.from_env()
            self.assertEqual(configured.jwt_secret, self.jwt.read_text())
            self.assertEqual(configured.admin_password_hash, PASSWORD_HASH)
            self.assertEqual(configured.trusted_proxy_ips, ('127.0.0.1', '::1'))
            self.assertEqual(configured.source_repositories[-1], 'owner/explicit-source')
            target.chmod(0o644)
            with self.assertRaises(ConfigurationError):
                Config.from_env()
        target.chmod(0o600)
        alias = self.directory / 'hash-alias'
        alias.symlink_to(target)
        with self.assertRaises(ConfigurationError):
            read_private_file(alias)
        fifo = self.directory / 'fifo'
        os.mkfifo(fifo, 0o600)
        with self.assertRaises(ConfigurationError):
            read_private_file(fifo)  # O_NONBLOCK ensures a non-file cannot hang startup.
        with patch.dict(os.environ, {'STUDY_PUBLIC_ORIGIN': 'https://study.example', 'STUDY_ADMIN_USERNAME': 'admin', 'STUDY_JWT_SECRET': self.jwt.read_text(), 'STUDY_ADMIN_PASSWORD_HASH': PASSWORD_HASH}, clear=True):
            self.assertTrue(Config.from_env().validate())


if __name__ == '__main__':
    unittest.main()
