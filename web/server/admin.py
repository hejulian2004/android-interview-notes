"""Interactive owner-only administrator initialization. Never starts an HTTP endpoint.

The operator supplies the password in a real terminal; no password argument, default
password, secret printing, credential discovery, or JWT replacement is supported.
"""
from __future__ import annotations
import argparse
import getpass
import os
from pathlib import Path
import secrets
import stat
import sys
import warnings
from .auth import hash_password


class InitializationError(ValueError):
    pass


def _private_metadata(metadata, *, directory=False):
    return (metadata.st_uid == os.getuid() and metadata.st_mode & 0o077 == 0
            and (stat.S_ISDIR(metadata.st_mode) if directory else stat.S_ISREG(metadata.st_mode)))


def _existing_file(directory_fd, name, *, required=False):
    try:
        metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        if required:
            raise InitializationError('请先由已获授权的部署步骤准备 jwt-secret 文件；初始化不会生成或替换签名密钥') from None
        return False
    if not _private_metadata(metadata) or metadata.st_size > 16384:
        raise InitializationError('已有配置文件不是当前用户拥有的私密普通文件')
    if name == 'jwt-secret' and metadata.st_size < 32:
        raise InitializationError('已有 JWT 密钥文件长度不符合要求；初始化不会替换该文件')
    return True


def initialize(directory, *, username=None, replace=False, password_prompt=None, username_prompt=None):
    """Write only a PBKDF2 password hash; requires an existing JWT file (metadata only).

    Prompt callbacks are injectable solely for tests; the CLI enforces a real TTY and
    getpass failure aborts before a fallback could echo the password.
    """
    directory = Path(directory)
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError:
        pass
    except OSError:
        raise InitializationError('无法创建私密配置目录，请检查其父目录和权限') from None
    try:
        directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | getattr(os, 'O_NOFOLLOW', 0))
    except OSError:
        raise InitializationError('配置目录不可用，不能使用符号链接') from None
    lock_acquired = False
    temporary_name = None
    try:
        if not _private_metadata(os.fstat(directory_fd), directory=True):
            raise InitializationError('配置目录必须由当前用户拥有，并且不允许其他用户访问（0700）')
        _existing_file(directory_fd, 'jwt-secret', required=True)
        exists = _existing_file(directory_fd, 'admin-password-hash')
        if exists and not replace:
            raise InitializationError('管理员凭据已存在；确需改密码时请显式使用 --replace')
        try:
            lock = os.open('admin-init.lock', os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600, dir_fd=directory_fd)
            os.close(lock)
            lock_acquired = True
        except OSError:
            raise InitializationError('另一个初始化正在进行或锁文件尚未清理，请先核实') from None
        if username is None:
            username = (username_prompt or input)('管理员用户名：').strip()
        if not isinstance(username, str) or not 1 <= len(username) <= 128 or any(ord(ch) < 33 or ord(ch) == 127 for ch in username):
            raise InitializationError('用户名应为 1–128 字，不能包含空白或控制字符')
        prompt = password_prompt or getpass.getpass
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            first = prompt('管理员密码（至少 12 字，不显示输入）：')
            second = prompt('再次输入管理员密码：')
        if first != second:
            raise InitializationError('两次密码不一致，未写入管理员凭据')
        try:
            encoded = hash_password(first)
        except ValueError:
            raise InitializationError('密码至少 12 字且不超过 1024 字节，未写入管理员凭据') from None
        # No plaintext is persisted. Atomic replacement uses the validated directory fd.
        temporary_name = '.admin-hash-' + secrets.token_hex(12)
        fd = os.open(temporary_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600, dir_fd=directory_fd)
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(encoded + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        # Refuse a concurrently inserted unsafe target even though replacement itself
        # would not follow it; this keeps operator intent and metadata checks explicit.
        if _existing_file(directory_fd, 'admin-password-hash') and not replace:
            raise InitializationError('管理员凭据已在初始化期间建立，未覆盖该文件')
        os.replace(temporary_name, 'admin-password-hash', src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        temporary_name = None
        os.fsync(directory_fd)
        return {'ready': True, 'username': username}
    except getpass.GetPassWarning:
        raise InitializationError('终端无法保证密码隐藏输入，已停止初始化') from None
    except OSError:
        raise InitializationError('凭据文件写入失败，请检查私密目录权限') from None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except OSError:
                pass
        if lock_acquired:
            try:
                os.unlink('admin-init.lock', dir_fd=directory_fd)
            except OSError:
                pass
        os.close(directory_fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Initialize a single local administrator without printing secrets')
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('initialize')
    command.add_argument('--directory', required=True)
    command.add_argument('--username')
    command.add_argument('--replace', action='store_true', help='Explicitly replace an existing administrator password hash')
    args = parser.parse_args(argv)
    if not sys.stdin.isatty():
        parser.error('请在交互式终端中运行；不接受管道或命令行密码')
    try:
        result = initialize(args.directory, username=args.username, replace=args.replace)
    except InitializationError as exc:
        parser.error(str(exc))
    print('管理员密码哈希已就绪；用户名：' + result['username'] + '。JWT 密钥保持原样，未输出任何密钥。')


if __name__ == '__main__':
    main()
