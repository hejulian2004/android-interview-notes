"""Bounded private JSON disk cache. This stores content, never credentials or grants.

All consumers of the same root share one disk budget. Application-level repository,
commit, path and blob validation remains mandatory before returning cached content.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import threading
import time

_LOCKS = {}
_PINS = {}
_LOCKS_LOCK = threading.Lock()
_PATTERN = re.compile(r'cache-[a-f0-9]{64}\.json\Z')


class DiskCache:
    SCHEMA = 1
    MAX_ENTRY_BYTES = 24_000_000

    def __init__(self, root, namespace, max_bytes=64_000_000, max_age=30 * 86400, clock=time.time, retained_keys=()):
        root = Path(root)
        if not root.is_absolute() or not isinstance(namespace, str) or not namespace or len(namespace) > 200:
            raise ValueError('Private content cache requires an absolute root and namespace')
        # Never follow a configured symlink, including existing parent components.
        for part in (root, *root.parents):
            if part.is_symlink():
                raise ValueError('Private content cache path must not contain symlinks')
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = root.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Private content cache root must be owner-only')
        if not 1024 <= max_bytes <= 512_000_000 or not 60 <= max_age <= 90 * 86400:
            raise ValueError('Private content cache bounds are invalid')
        self.root, self.namespace, self.max_bytes, self.max_age, self.clock = root, namespace, max_bytes, max_age, clock
        with _LOCKS_LOCK:
            root_key = str(root.resolve())
            self._lock = _LOCKS.setdefault(root_key, threading.RLock())
            self._pins = _PINS.setdefault(root_key, set())
            self._pins.update(self._path(key).name for key in retained_keys)

    @staticmethod
    def _encoded(value):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')

    def _path(self, key):
        if not isinstance(key, str) or len(key) > 4096:
            raise ValueError('Cache key is invalid')
        digest = hashlib.sha256(self._encoded([self.namespace, key])).hexdigest()
        return self.root / ('cache-' + digest + '.json')

    def _remove(self, path):
        try:
            if path.parent == self.root and _PATTERN.fullmatch(path.name):
                path.unlink(missing_ok=True)
        except OSError:
            pass

    def get(self, key):
        path = self._path(key)
        with self._lock:
            try:
                descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(descriptor, 'rb') as stream:
                    info = os.fstat(stream.fileno())
                    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                            or info.st_mode & 0o077 or info.st_size > min(self.MAX_ENTRY_BYTES, self.max_bytes)):
                        raise ValueError('Unsafe cache entry')
                    raw = stream.read(self.MAX_ENTRY_BYTES + 1)
                value = json.loads(raw)
                if (not isinstance(value, dict) or value.get('schema') != self.SCHEMA
                        or value.get('namespace') != self.namespace or value.get('key') != key
                        or type(value.get('savedAt')) not in (int, float)
                        or not 0 <= self.clock() - value['savedAt'] <= self.max_age
                        or value.get('sha256') != hashlib.sha256(self._encoded(value['payload'])).hexdigest()):
                    raise ValueError('Invalid cache envelope')
                return value['payload']
            except FileNotFoundError:
                return None
            except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
                self._remove(path)
                return None

    def put(self, key, payload):
        path, temp = self._path(key), None
        try:
            body = self._encoded(payload)
            raw = self._encoded({'schema': self.SCHEMA, 'namespace': self.namespace, 'key': key,
                'savedAt': self.clock(), 'sha256': hashlib.sha256(body).hexdigest(), 'payload': payload})
            if len(raw) > min(self.MAX_ENTRY_BYTES, self.max_bytes):
                return False
            with self._lock:
                descriptor, temp = tempfile.mkstemp(prefix='.cache-write-', dir=self.root)
                with os.fdopen(descriptor, 'wb') as stream:
                    os.fchmod(stream.fileno(), 0o600)
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp, path)
                temp = None
                self._cleanup(protect=path)
                return True
        except (OSError, ValueError, TypeError, RecursionError):
            return False
        finally:
            if temp is not None:
                try:
                    os.unlink(temp)
                except OSError:
                    pass

    def delete(self, key):
        with self._lock:
            self._remove(self._path(key))

    def _cleanup(self, protect=None):
        # Do not recursively walk or touch Git objects, private configs, or files
        # outside our exact hash naming convention. Symlinks are unlinked only.
        entries, total, now = [], 0, self.clock()
        for path in self.root.iterdir():
            if not _PATTERN.fullmatch(path.name):
                continue
            try:
                info = path.lstat()
            except OSError:
                continue
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or info.st_mode & 0o077 or now - info.st_mtime > self.max_age):
                if path != protect:
                    self._remove(path)
                continue
            entries.append((info.st_mtime, path, info.st_size))
            total += info.st_size
        for _, path, size in sorted(entries, key=lambda item: (item[1].name in self._pins, item[0], item[1].name)):
            if total <= self.max_bytes:
                break
            if path != protect:
                self._remove(path)
                total -= size
