import json
from types import SimpleNamespace

import pytest

from onehealth_worker.extraction import file_pipeline
from test_attribution_review import artifacts


@pytest.mark.parametrize('invalid', ['duplicate_top', 'duplicate_nested', 'NaN', 'Infinity', '-Infinity', '1e999'])
@pytest.mark.parametrize('persist', [False, True])
def test_ambiguous_or_nonfinite_json_rejected_before_repository(tmp_path, monkeypatch, invalid, persist):
    fixture = artifacts()
    encoded = fixture['signals_bytes'].decode()
    if invalid == 'duplicate_top':
        encoded = '{"schema_version":"ambiguous",' + encoded[1:]
    elif invalid == 'duplicate_nested':
        encoded = encoded.replace('"raw_item_id":', '"raw_item_id":"ambiguous","raw_item_id":', 1)
    else:
        payload = json.loads(encoded)
        payload['signals'][0]['metrics'][0]['value_numeric'] = 'SYNTHETIC_NUMBER'
        encoded = json.dumps(payload).replace('"SYNTHETIC_NUMBER"', invalid)
    path = tmp_path / 'extraction.json'
    path.write_text(encoded, encoding='utf-8')
    original = path.read_bytes()

    def forbidden_repository(*args, **kwargs):
        raise AssertionError('Invalid JSON reached repository')

    monkeypatch.setattr(file_pipeline, 'ExtractionRepository', forbidden_repository)
    with pytest.raises(ValueError, match='JSON'):
        if persist:
            file_pipeline.persist_file(database_url='unused', path=path)
        else:
            file_pipeline.validate_file(path)
    assert path.read_bytes() == original


@pytest.mark.parametrize('value', [3, 0.75])
def test_valid_integer_and_fractional_json_values_are_preserved(tmp_path, value):
    payload = json.loads(artifacts()['signals_bytes'])
    payload['signals'][0]['metrics'][0]['value_numeric'] = value
    path = tmp_path / 'valid.json'
    path.write_text(json.dumps(payload), encoding='utf-8')
    assert file_pipeline.validate_file(path) == payload


def test_valid_file_reaches_fake_persistence_with_source_evidence_validation(tmp_path, monkeypatch):
    fixture = artifacts()
    path = tmp_path / 'valid.json'
    path.write_bytes(fixture['signals_bytes'])
    payload = json.loads(fixture['signals_bytes'])
    calls = []

    class Repository:
        def __init__(self, dsn):
            assert dsn == 'unused'

        def load_raw_document(self, identifier):
            assert identifier == payload['document']['raw_item_id']
            return SimpleNamespace(raw_text=fixture['raw_text'])

        def persist_extraction(self, **kwargs):
            calls.append(kwargs)
            return 'synthetic-run', []

    monkeypatch.setattr(file_pipeline, 'ExtractionRepository', Repository)
    assert file_pipeline.persist_file(database_url='unused', path=path) == ('synthetic-run', [])
    assert len(calls) == 1
    assert calls[0]['payload'] == payload
