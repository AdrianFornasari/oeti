import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from onehealth_worker.evaluation.offline import run_frozen_corpus


def manifest(tmp_path, count=1):
    root = tmp_path / 'frozen'
    root.mkdir()
    documents = []
    for index in range(count):
        raw = f'Documento {index}: evidencia literal H5.\n'.encode()
        (root / f'{index}.txt').write_bytes(raw)
        documents.append({'document_id': f'D{index}', 'title': f'Documento {index}',
            'requested_url': f'https://example.invalid/{index}', 'declared_page_date': None,
            'evaluation_input_path': f'{index}.txt', 'evaluation_input_sha256': hashlib.sha256(raw).hexdigest()})
    path = root / 'freeze.json'
    path.write_text(json.dumps({'case_code': 'TEST', 'documents': documents,
        'proposed_run': {'model': 'test-model', 'evaluation_scope': 'Solo H5'}}), encoding='utf-8')
    return path


class FakeProvider:
    def __init__(self, wrong_binding=False):
        self.calls = []
        self.wrong_binding = wrong_binding

    def extract(self, **kwargs):
        self.calls.append(kwargs)
        raw_id = kwargs['document_input'].splitlines()[0].removeprefix('RAW_ITEM_ID: ')
        return SimpleNamespace(payload={'schema_version': 'claims-0.1',
            'document': {'raw_item_id': 'wrong' if self.wrong_binding else raw_id,
                         'language': 'es', 'document_date': None}, 'claims': [], 'warnings': []},
            response_id='fake-response', usage={'input_tokens': 7, 'output_tokens': 3, 'total_tokens': 10})


def test_default_only_prepares_inputs_without_provider(tmp_path):
    path = manifest(tmp_path)
    provider = FakeProvider()
    report = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'plan', provider=provider)
    assert provider.calls == []
    assert report['mode'] == 'prepare_only'
    assert report['evaluation_class'] == 'exploratory_no_independent_review'
    assert report['results'][0]['status'] == 'prepared'
    text = (tmp_path/'plan/001.input.txt').read_text(encoding='utf-8')
    assert 'DOCUMENT_TEXT_BEGIN\nDocumento 0: evidencia literal H5.\n' in text
    assert 'PUBLISHED_AT: unknown' in text
    assert 'EVALUATION_SCOPE_BEGIN' in text
    assert not list((tmp_path/'plan').glob('*.claims.json'))


def test_binding_is_deterministic_and_changes_with_source_hash(tmp_path):
    path = manifest(tmp_path)
    first = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'one')
    second = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'two')
    assert first['results'][0]['raw_item_id'] == second['results'][0]['raw_item_id']
    assert first['results'][0]['input_sha256'] == second['results'][0]['input_sha256']
    payload = json.loads(path.read_text())
    changed = b'New frozen source.\n'
    (path.parent/'0.txt').write_bytes(changed)
    payload['documents'][0]['evaluation_input_sha256'] = hashlib.sha256(changed).hexdigest()
    path.write_text(json.dumps(payload))
    third = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'three')
    assert third['results'][0]['raw_item_id'] != first['results'][0]['raw_item_id']


def test_all_hashes_are_checked_before_any_provider_call_or_output(tmp_path):
    path = manifest(tmp_path, 2)
    (path.parent/'1.txt').write_text('changed', encoding='utf-8')
    provider = FakeProvider()
    with pytest.raises(ValueError, match='hash'):
        run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'run', execute=True, provider=provider)
    assert provider.calls == []
    assert not (tmp_path/'run').exists()


@pytest.mark.parametrize('field,value', [('evaluation_input_path', '../outside.txt'),
    ('evaluation_input_path', '/absolute.txt'), ('evaluation_input_sha256', 'invalid')])
def test_invalid_source_reference_fails_closed(tmp_path, field, value):
    path = manifest(tmp_path)
    payload = json.loads(path.read_text())
    payload['documents'][0][field] = value
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'run')
    assert not (tmp_path/'run').exists()


def test_refuses_existing_output_or_output_inside_sources(tmp_path):
    path = manifest(tmp_path)
    (tmp_path/'existing').mkdir()
    (tmp_path/'existing/keep').write_text('original')
    with pytest.raises(ValueError):
        run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'existing')
    with pytest.raises(ValueError):
        run_frozen_corpus(manifest_path=path, output_dir=path.parent/'run')
    assert (tmp_path/'existing/keep').read_text() == 'original'


def test_duplicate_documents_are_not_silently_counted_twice(tmp_path):
    path = manifest(tmp_path)
    payload = json.loads(path.read_text())
    payload['documents'] *= 2
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match='duplicate'):
        run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'run')


def test_execute_requires_an_explicit_injected_provider(tmp_path):
    path = manifest(tmp_path)
    with pytest.raises(ValueError, match='provider'):
        run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'run', execute=True)
    assert not (tmp_path/'run').exists()


def test_fake_response_uses_production_assembly_and_retains_usage(tmp_path):
    path = manifest(tmp_path)
    provider = FakeProvider()
    report = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'run', execute=True, provider=provider)
    result = report['results'][0]
    assert len(provider.calls) == 1
    assert result['status'] == 'generated'
    assert result['usage']['total_tokens'] == 10
    signals = json.loads((tmp_path/'run/001.signals.json').read_text())
    assert signals['document']['raw_item_id'] == result['raw_item_id']
    assert signals['signals'] == []


def test_validation_failure_preserves_response_usage_without_accepting_signals(tmp_path):
    path = manifest(tmp_path)
    report = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'run', execute=True,
                               provider=FakeProvider(wrong_binding=True))
    result = report['results'][0]
    assert result['status'] == 'failed'
    assert result['usage']['total_tokens'] == 10
    assert (tmp_path/'run/001.claims.json').exists()
    assert not (tmp_path/'run/001.signals.json').exists()
    assert result['error_type'] == 'ValueError'


def test_frozen_code_mismatch_is_rejected_before_output(tmp_path):
    path = manifest(tmp_path)
    payload = json.loads(path.read_text())
    payload['code_freeze'] = {'files': [{'path': 'services/worker/pyproject.toml', 'sha256': '0'*64}]}
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match='code hash'):
        run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'run')
    assert not (tmp_path/'run').exists()


def test_provider_failure_is_redacted_and_does_not_skip_later_documents(tmp_path):
    path = manifest(tmp_path, 2)
    class SometimesFails(FakeProvider):
        def extract(self, **kwargs):
            if not self.calls:
                self.calls.append(kwargs)
                raise RuntimeError('secret-api-key-do-not-save')
            return super().extract(**kwargs)
    report = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'run', execute=True, provider=SometimesFails())
    assert [r['status'] for r in report['results']] == ['failed', 'generated']
    assert report['summary'] == {'prepared': 0, 'generated': 1, 'failed': 1}
    assert report['results'][0]['usage'] is None
    assert 'secret-api-key' not in (tmp_path/'run/report.json').read_text()


def test_cli_prepares_without_settings_or_network(tmp_path, monkeypatch, capsys):
    from onehealth_worker.evaluation.offline import main
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError('Network is forbidden')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('LLM_API_KEY', raising=False)
    path = manifest(tmp_path)
    main(['--manifest', str(path), '--output', str(tmp_path/'plan')])
    assert json.loads(capsys.readouterr().out)['mode'] == 'prepare_only'
