"""Explicit runtime configuration. Importing this module never reads credentials."""
from __future__ import annotations
from dataclasses import dataclass, field
import ipaddress
import os
import re
from pathlib import Path
from urllib.parse import urlsplit


class ConfigurationError(ValueError):
    pass


@dataclass
class Config:
    public_origin: str = ''
    jwt_secret: str = field(default='', repr=False)
    admin_username: str = ''
    admin_password_hash: str = field(default='', repr=False)
    access_seconds: int = 900
    refresh_seconds: int = 7 * 24 * 3600
    api_prefix: str = '/android-study/api'
    secure_cookies: bool = True
    allow_insecure_local_dev: bool = False
    static_root: str | None = None
    max_body_bytes: int = 524288
    login_attempts: int = 5
    login_window_seconds: int = 900
    login_bucket_limit: int = 4096
    trusted_proxy_ips: tuple[str, ...] = ()
    source_repositories: tuple[str, ...] = ('hejulian2004/android-interview-notes',)
    model_allowed_hosts: tuple[str, ...] = ()
    model_internal_endpoints: tuple[str, ...] = ()
    model_base_url: str = ''
    model_name: str = ''
    model_api_key: str = field(default='', repr=False)
    github_token_file: str = field(default='', repr=False)
    github_transport: str = 'https'
    github_cache_root: str = ''
    data_cache_root: str = ''
    github_write_enabled: bool = False

    def validate(self):
        if self.github_transport not in ('https', 'ssh') or type(self.github_write_enabled) is not bool:
            raise ConfigurationError('Invalid GitHub transport or explicit write permission')
        if self.github_transport == 'ssh' and (not self.github_cache_root or not Path(self.github_cache_root).is_absolute()):
            raise ConfigurationError('SSH transport requires an explicit absolute private cache root')
        if self.data_cache_root and not Path(self.data_cache_root).is_absolute():
            raise ConfigurationError('Data cache root must be an absolute private directory')
        p = urlsplit(self.public_origin)
        local_dev = self.allow_insecure_local_dev and p.hostname in ('localhost', '127.0.0.1', '::1')
        if not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in ('', '/'):
            raise ConfigurationError('STUDY_PUBLIC_ORIGIN must be an exact origin without a path')
        if p.scheme != 'https' and not (local_dev and p.scheme == 'http'):
            raise ConfigurationError('HTTPS origin is required')
        if self.public_origin.endswith('/'):
            raise ConfigurationError('Origin must not have a trailing slash')
        if not self.secure_cookies and not local_dev:
            raise ConfigurationError('Secure cookies may only be disabled for explicit loopback development')
        if not isinstance(self.jwt_secret, str) or len(self.jwt_secret.encode()) < 32:
            raise ConfigurationError('Explicit JWT signing secret of at least 32 bytes is required')
        if not self.admin_username or len(self.admin_username) > 128:
            raise ConfigurationError('Explicit administrator username is required')
        from .auth import valid_password_hash
        if not valid_password_hash(self.admin_password_hash):
            raise ConfigurationError('Explicit supported administrator password hash is required')
        if not (60 <= self.access_seconds <= 3600) or not (self.access_seconds < self.refresh_seconds <= 30 * 86400):
            raise ConfigurationError('Session lifetime is out of bounds')
        if not self.api_prefix.startswith('/') or self.api_prefix.endswith('/') or '..' in self.api_prefix:
            raise ConfigurationError('Invalid API prefix')
        if not 1024 <= self.max_body_bytes <= 2 * 1024 * 1024:
            raise ConfigurationError('Invalid request size limit')
        if not 1 <= self.login_attempts <= 50 or not 10 <= self.login_window_seconds <= 3600:
            raise ConfigurationError('Invalid login rate limit')
        if not 1 <= self.login_bucket_limit <= 100000:
            raise ConfigurationError('Invalid login bucket limit')
        try:
            if any('%' in value for value in self.trusted_proxy_ips):
                raise ValueError()
            self.trusted_proxy_ips = tuple(str(ipaddress.ip_address(value)) for value in self.trusted_proxy_ips)
        except (ValueError, TypeError):
            raise ConfigurationError('Trusted proxies must be explicit numeric IP addresses') from None
        if (not isinstance(self.source_repositories, tuple) or len(self.source_repositories) > 20
                or any(not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value) for value in self.source_repositories)):
            raise ConfigurationError('Invalid explicit source repository allowlist')
        return self

    @classmethod
    def from_env(cls):
        # Intentionally called only by the explicit server entry point, never at import.
        return cls(
            public_origin=os.environ.get('STUDY_PUBLIC_ORIGIN', ''),
            jwt_secret=private_value_from_env('STUDY_JWT_SECRET', 'STUDY_JWT_SECRET_FILE'),
            admin_username=os.environ.get('STUDY_ADMIN_USERNAME', ''),
            admin_password_hash=private_value_from_env('STUDY_ADMIN_PASSWORD_HASH', 'STUDY_ADMIN_PASSWORD_HASH_FILE'),
            trusted_proxy_ips=tuple(x.strip() for x in os.environ.get('STUDY_TRUSTED_PROXY_IPS', '').split(',') if x.strip()),
            source_repositories=tuple(x.strip() for x in os.environ.get('STUDY_SOURCE_REPOSITORIES', 'hejulian2004/android-interview-notes').split(',') if x.strip()),
            static_root=os.environ.get('STUDY_STATIC_ROOT') or None,
            model_allowed_hosts=tuple(x.strip().lower() for x in os.environ.get('STUDY_MODEL_ALLOWED_HOSTS', '').split(',') if x.strip()),
            model_internal_endpoints=tuple(x.strip() for x in os.environ.get('STUDY_MODEL_INTERNAL_ENDPOINTS', '').split(',') if x.strip()),
            model_base_url=os.environ.get('STUDY_MODEL_BASE_URL', ''),
            model_name=os.environ.get('STUDY_MODEL_NAME', ''),
            model_api_key=os.environ.get('STUDY_MODEL_API_KEY', ''),
            github_token_file=os.environ.get('STUDY_GITHUB_TOKEN_FILE', ''),
            github_transport=os.environ.get('STUDY_GITHUB_TRANSPORT', 'https'),
            github_cache_root=os.environ.get('STUDY_GITHUB_CACHE_ROOT', ''),
            data_cache_root=os.environ.get('STUDY_DATA_CACHE_ROOT', ''),
            github_write_enabled=os.environ.get('STUDY_GITHUB_WRITE_ENABLED') == '1',
            allow_insecure_local_dev=os.environ.get('STUDY_ALLOW_INSECURE_LOCAL_DEV') == '1',
            secure_cookies=os.environ.get('STUDY_ALLOW_INSECURE_LOCAL_DEV') != '1',
        ).validate()


def require_loopback(host: str):
    """Do not expose the application server directly to a public interface."""
    try:
        if not ipaddress.ip_address(host).is_loopback:
            raise ConfigurationError('Application listener must use a numeric loopback address')
    except ValueError as exc:
        raise ConfigurationError('Application listener must use a numeric loopback address') from exc


def read_private_file(path):
    """Read an explicitly selected owner-only regular file; return no path in errors."""
    import stat
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(fd, 'r', encoding='utf-8') as handle:
            metadata = os.fstat(handle.fileno())
            if (not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077
                    or metadata.st_uid != os.getuid() or metadata.st_size > 16384):
                raise ValueError()
            value = handle.read(16385).strip()
            if not value or len(value) > 16384 or '\n' in value or '\r' in value:
                raise ValueError()
            return value
    except (OSError, ValueError, UnicodeError):
        raise ConfigurationError('Explicit private configuration file is unavailable or unsafe') from None


def private_value_from_env(inline_name, file_name):
    path = os.environ.get(file_name, '')
    # An explicitly selected file has precedence; a bad file never falls back to inline.
    return read_private_file(path) if path else os.environ.get(inline_name, '')


def github_token_provider(config: Config):
    """Only an explicitly selected runtime file; no discovery or shell helper."""
    def read():
        from .auth import AuthError
        if not config.github_token_file:
            raise AuthError('github_not_configured', 'GitHub 服务端凭据尚未配置', 503)
        try:
            return read_private_file(config.github_token_file)
        except ConfigurationError:
            raise AuthError('github_not_configured', 'GitHub 服务端凭据不可用，请由管理员检查配置', 503) from None
    return read
