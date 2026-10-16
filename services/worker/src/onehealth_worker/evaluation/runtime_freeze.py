"""Optional declared-version preflight; no installation or network operations."""
import hashlib
from importlib import metadata
from pathlib import Path
import platform
import re


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?', value):
        raise ValueError('invalid runtime distribution name')
    return re.sub(r'[-_.]+', '-', value).lower()


def verify_runtime_freeze(freeze, *, repository_root: Path) -> dict:
    """Verify only declared packages and lock bytes, not full environment integrity."""
    if not isinstance(freeze, dict) or set(freeze) - {'version', 'python', 'distributions', 'locks'}:
        raise ValueError('invalid runtime_freeze contract')
    if type(freeze.get('version')) is not int or freeze['version'] != 1:
        raise ValueError('unsupported runtime_freeze version')
    python = freeze.get('python')
    if not isinstance(python, str) or not re.fullmatch(r'\d+\.\d+\.\d+', python):
        raise ValueError('exact Python version required')
    if python != platform.python_version():
        raise ValueError('frozen Python version mismatch')
    entries = freeze.get('distributions')
    if not isinstance(entries, list) or not entries:
        raise ValueError('runtime distributions must be nonempty')
    required = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {'name', 'version'}:
            raise ValueError('invalid runtime distribution entry')
        name = _name(entry['name'])
        version = entry['version']
        if not isinstance(version, str) or not version.strip() or version != version.strip():
            raise ValueError('exact distribution version required')
        if name in required:
            raise ValueError('duplicate runtime distribution')
        required[name] = version
    installed = {name: [] for name in required}
    for dist in metadata.distributions():
        name = dist.metadata.get('Name')
        if not name:
            continue  # Unidentified metadata cannot satisfy any requirement.
        name = _name(name)
        if name in installed:
            installed[name].append(dist.metadata.get('Version'))
    if any(installed[name] != [version] for name, version in required.items()):
        raise ValueError('frozen distribution missing, ambiguous or version mismatch')
    root = repository_root.resolve()
    locks = freeze.get('locks', [])
    if not isinstance(locks, list):
        raise ValueError('runtime locks must be a list')
    verified_locks, seen = [], set()
    for entry in locks:
        if not isinstance(entry, dict) or set(entry) != {'path', 'sha256'}:
            raise ValueError('invalid runtime lock entry')
        relative, digest = entry['path'], entry['sha256']
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise ValueError('runtime lock path must be relative')
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or path in seen:
            raise ValueError('runtime lock path escapes repository or is duplicated')
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('invalid runtime lock hash')
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('runtime lock hash mismatch')
        seen.add(path)
        verified_locks.append({'path': path.relative_to(root).as_posix(), 'sha256': digest})
    return {'version': 1, 'python': python,
            'distributions': [{'name': name, 'version': version} for name, version in sorted(required.items())],
            'locks': verified_locks, 'scope': 'declared_versions_and_lock_bytes_only'}
