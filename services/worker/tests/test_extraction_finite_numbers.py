import json
from types import SimpleNamespace

import pytest

from onehealth_worker.extraction import pipeline
from onehealth_worker.extraction.schema import (
    ExtractionSchemaError, validate_atomic_claims, validate_extraction,
)
from test_attribution_review import artifacts
from test_extraction_document_date_binding import fake_services


def payload_and_metric(kind):
    fixture = artifacts()
    if kind == 'claims':
        payload = json.loads(fixture['claims_bytes'])
        return payload, payload['claims'][0]['metric'], validate_atomic_claims
    payload = json.loads(fixture['signals_bytes'])
    return payload, payload['signals'][0]['metrics'][0], validate_extraction


@pytest.mark.parametrize('kind', ['claims', 'signals'])
@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf')])
def test_decoded_nonfinite_metric_is_rejected(kind, value):
    payload, metric, validate = payload_and_metric(kind)
    metric['value_numeric'] = value
    with pytest.raises(ExtractionSchemaError, match='finito'):
        validate(payload)


@pytest.mark.parametrize('kind', ['claims', 'signals'])
@pytest.mark.parametrize('value', [0, 3, 0.75, None])
def test_valid_numeric_values_and_literal_text_are_unchanged(kind, value):
    payload, metric, validate = payload_and_metric(kind)
    metric['value_numeric'] = value
    metric['value_text'] = 'NaN es texto literal, no un valor numérico.'
    before = json.dumps(payload, allow_nan=False)
    validate(payload)
    assert json.dumps(payload, allow_nan=False) == before


@pytest.mark.parametrize('persist', [False, True])
@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf')])
def test_nonfinite_provider_metric_never_reaches_successful_persistence(monkeypatch, persist, value):
    document, failed, persisted, usage = fake_services(monkeypatch, None, None)
    claims = json.loads(artifacts()['claims_bytes'])
    claims['document']['document_date'] = None
    claims['claims'][0]['metric']['value_numeric'] = value
    response = SimpleNamespace(payload=claims, response_id='synthetic-response', usage=usage)
    monkeypatch.setattr(pipeline, 'OpenAIResponsesProvider',
        lambda **kwargs: SimpleNamespace(extract=lambda **arguments: response))
    with pytest.raises(ExtractionSchemaError, match='finito'):
        pipeline.extract_raw_item(database_url='unused', raw_item_id=document.raw_item_id,
            provider_name='openai', model_name='synthetic', api_key='unused', persist=persist)
    assert persisted == []
    assert len(failed) == int(persist)
    if persist:
        assert failed[0]['usage'] == usage
        assert failed[0]['response_id'] == 'synthetic-response'
