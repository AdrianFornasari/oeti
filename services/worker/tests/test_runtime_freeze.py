import hashlib
import json
from types import SimpleNamespace

import pytest

from test_offline_frozen_corpus import manifest, FakeProvider
from onehealth_worker.evaluation import runtime_freeze as runtime, offline


@pytest.fixture
def contract(monkeypatch):
    monkeypatch.setattr(runtime.platform, 'python_version', lambda: '3.13.8')
    monkeypatch.setattr(runtime.metadata, 'distributions', lambda: [
        SimpleNamespace(metadata={'Name': 'Demo_Package', 'Version': '1.2.3'})])
    return {'version': 1, 'python': '3.13.8',
            'distributions': [{'name': 'demo-package', 'version': '1.2.3'}]}


def test_verifies_normalized_names_and_lock_bytes(contract, tmp_path):
    lock = tmp_path / 'test.lock'
    lock.write_bytes(b'example==1.2.3\n')
    contract['locks'] = [{'path': lock.name, 'sha256': hashlib.sha256(lock.read_bytes()).hexdigest()}]
    result = runtime.verify_runtime_freeze(contract, repository_root=tmp_path)
    assert result['distributions'] == contract['distributions']
    assert result['locks'] == contract['locks']
    assert result['scope'] == 'declared_versions_and_lock_bytes_only'


@pytest.mark.parametrize('change', [
    lambda c: c.update(python='3.12.1'),
    lambda c: c.update(python='3.13'),
    lambda c: c.update(version=True),
    lambda c: c.update(distributions=[]),
    lambda c: c['distributions'][0].update(version='2.0'),
    lambda c: c['distributions'][0].update(name='missing'),
    lambda c: c['distributions'].append({'name': 'Demo_Package', 'version': '1.2.3'}),
    lambda c: c.update(locks=None),
    lambda c: c.update(unknown=True),
    lambda c: c.update(locks=[{'path': '/absolute', 'sha256': '0'*64}]),
    lambda c: c.update(locks=[{'path': 'test.lock', 'sha256': 'invalid'}]),
    lambda c: c.update(locks=[{'path': '../escape', 'sha256': '0'*64}]),
    lambda c: c.update(locks=[{'path': 'test.lock', 'sha256': '0'*64}]),
])
def test_mismatches_fail_before_provider_or_output(contract, tmp_path, monkeypatch, change):
    path = manifest(tmp_path)
    monkeypatch.setattr(offline, 'REPOSITORY_ROOT', tmp_path)
    (tmp_path / 'test.lock').write_bytes(b'changed')
    change(contract)
    payload = json.loads(path.read_text())
    payload['runtime_freeze'] = contract
    path.write_text(json.dumps(payload))
    provider = FakeProvider()
    with pytest.raises(ValueError):
        offline.run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'run', execute=True, provider=provider)
    assert not provider.calls and not (tmp_path/'run').exists()


@pytest.mark.parametrize('records', [[], [{'Name': 'demo-package'}],
    [{'Name': 'demo-package', 'Version': '1.2.3'}]*2, [{'Version': '1.2.3'}]])
def test_missing_ambiguous_or_incomplete_metadata_fail(contract, tmp_path, monkeypatch, records):
    monkeypatch.setattr(runtime.metadata, 'distributions', lambda: [SimpleNamespace(metadata=r) for r in records])
    with pytest.raises(ValueError):
        runtime.verify_runtime_freeze(contract, repository_root=tmp_path)


def test_optional_report_and_legacy_contract(contract, tmp_path):
    path = manifest(tmp_path)
    legacy = offline.run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'legacy')
    assert 'verified_runtime_freeze' not in legacy
    data = json.loads(path.read_text())
    data['runtime_freeze'] = contract
    path.write_text(json.dumps(data))
    report = offline.run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'new')
    assert report['verified_runtime_freeze']['python'] == '3.13.8'
    assert report['results'][0]['status'] == 'prepared'


def test_duplicate_resolved_lock_paths_rejected(contract, tmp_path):
    lock = tmp_path / 'test.lock'
    lock.write_bytes(b'example')
    digest = hashlib.sha256(lock.read_bytes()).hexdigest()
    contract['locks'] = [{'path': 'test.lock', 'sha256': digest},
                         {'path': './test.lock', 'sha256': digest}]
    with pytest.raises(ValueError, match='duplicated'):
        runtime.verify_runtime_freeze(contract, repository_root=tmp_path)


def test_present_null_freeze_is_invalid(tmp_path):
    path = manifest(tmp_path)
    data = json.loads(path.read_text())
    data['runtime_freeze'] = None
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        offline.run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'run')
    assert not (tmp_path/'run').exists()
