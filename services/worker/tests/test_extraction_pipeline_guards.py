import json
from types import SimpleNamespace

import pytest

from onehealth_worker.extraction import pipeline
from test_attribution_review import artifacts
from test_extraction_document_date_binding import fake_services


@pytest.mark.parametrize('persist', [False, True])
@pytest.mark.parametrize('failure', ['schema', 'document_id', 'evidence', 'provider'])
def test_failed_extraction_never_becomes_successful_or_writes_in_nonpersisting_mode(
    monkeypatch, persist, failure,
):
    document, failed, persisted, usage = fake_services(monkeypatch, None, None)
    claims = json.loads(artifacts()['claims_bytes'])
    claims['document']['document_date'] = None
    if failure == 'schema':
        claims.pop('schema_version')
    elif failure == 'document_id':
        claims['document']['raw_item_id'] = '00000000-0000-4000-8000-000000000001'
    elif failure == 'evidence':
        claims['claims'][0]['evidence'][0]['text'] = 'Una cita sintética que no existe en el origen.'

    class Provider:
        def __init__(self, **kwargs):
            pass

        def extract(self, **kwargs):
            if failure == 'provider':
                raise RuntimeError('Synthetic provider failure')
            return SimpleNamespace(payload=claims, response_id='synthetic-response', usage=usage)

    monkeypatch.setattr(pipeline, 'OpenAIResponsesProvider', Provider)
    expected = {
        'schema': (ValueError, 'schema_version'),
        'document_id': (ValueError, 'raw_item_id'),
        'evidence': (ValueError, 'literal'),
        'provider': (RuntimeError, 'Synthetic provider failure'),
    }
    error_type, message = expected[failure]
    with pytest.raises(error_type, match=message) as error:
        pipeline.extract_raw_item(database_url='unused', raw_item_id=document.raw_item_id,
            provider_name='openai', model_name='synthetic', api_key='unused', persist=persist)
    assert persisted == []
    if persist:
        assert len(failed) == 1
        assert failed[0]['raw_item_id'] == document.raw_item_id
        assert failed[0]['error_text'] == str(error.value)
        assert failed[0]['usage'] == (None if failure == 'provider' else usage)
        assert failed[0]['response_id'] == (None if failure == 'provider' else 'synthetic-response')
    else:
        assert failed == []
