from datetime import datetime, timezone
import json
from types import SimpleNamespace

import pytest

from onehealth_worker.extraction import pipeline
from test_attribution_review import artifacts


def fake_services(monkeypatch, published_at, returned_date):
    fixture = artifacts()
    claims = json.loads(fixture['claims_bytes'])
    claims['document']['document_date'] = returned_date
    document = SimpleNamespace(raw_item_id=claims['document']['raw_item_id'], title='Synthetic',
        url='https://example.invalid/synthetic', published_at=published_at, language='es',
        raw_text=fixture['raw_text'])
    failed, persisted = [], []
    usage = {'input_tokens': 12, 'output_tokens': 4}

    class Repository:
        def __init__(self, dsn):
            assert dsn == 'unused'

        def load_raw_document(self, identifier):
            assert identifier == document.raw_item_id
            return document

        def record_failed_run(self, **kwargs):
            failed.append(kwargs)

        def persist_extraction(self, **kwargs):
            persisted.append(kwargs)
            return 'synthetic-run', []

    class Provider:
        def __init__(self, **kwargs):
            pass

        def extract(self, **kwargs):
            return SimpleNamespace(payload=claims, response_id='synthetic-response', usage=usage)

    monkeypatch.setattr(pipeline, 'ExtractionRepository', Repository)
    monkeypatch.setattr(pipeline, 'OpenAIResponsesProvider', Provider)
    return document, failed, persisted, usage


@pytest.mark.parametrize('published_at,returned_date', [
    (None, '2026-05-04'),
    (datetime(2026, 5, 4, 12, tzinfo=timezone.utc), '2025-01-01'),
    (datetime(2026, 5, 4, 12, tzinfo=timezone.utc), None),
])
@pytest.mark.parametrize('persist', [False, True])
def test_changed_document_date_rejected_before_successful_persistence(monkeypatch, published_at, returned_date, persist):
    document, failed, persisted, usage = fake_services(monkeypatch, published_at, returned_date)
    with pytest.raises(ValueError, match='document_date'):
        pipeline.extract_raw_item(database_url='unused', raw_item_id=document.raw_item_id,
            provider_name='openai', model_name='synthetic', api_key='unused', persist=persist)
    assert persisted == []
    if persist:
        assert len(failed) == 1
        assert failed[0]['usage'] == usage
        assert failed[0]['response_id'] == 'synthetic-response'
    else:
        assert failed == []


@pytest.mark.parametrize('published_at,returned_date', [
    (None, None),
    (datetime(2026, 5, 4, 12, tzinfo=timezone.utc), '2026-05-04'),
])
@pytest.mark.parametrize('persist', [False, True])
def test_matching_document_date_preserves_normal_flow(monkeypatch, published_at, returned_date, persist):
    document, failed, persisted, _ = fake_services(monkeypatch, published_at, returned_date)
    result = pipeline.extract_raw_item(database_url='unused', raw_item_id=document.raw_item_id,
        provider_name='openai', model_name='synthetic', api_key='unused', persist=persist)
    assert result.persisted is persist
    assert result.payload['document']['document_date'] == returned_date
    assert len(persisted) == int(persist)
    assert failed == []
